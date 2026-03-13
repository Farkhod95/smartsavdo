from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from collections import OrderedDict
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from rest_framework.generics import ListAPIView

from inventory.models import Product, ProductStock
from sales.filterset import VozvratOrderFilter
from sales.models import VozvratOrder, OrderHistoryProduct, Order, Client
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.vozvrat_order import VozvratOrderSerializer, VozvratOrderListSerializer, \
    VozvratOrderUpdateSerializer, VozvratOrderReturnSerializer


class VozvratOrderFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in VozvratOrder._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class VozvratOrderViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = VozvratOrderSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return VozvratOrder.objects.filter(is_delete=False)


class VozvratOrderGroupedByDateView(ListAPIView):
    serializer_class = VozvratOrderListSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-created_time', '-pk']  # ichida tartib

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            VozvratOrder.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'client', 'employee', 'created_by')
            .order_by('-created_time', '-pk')
        )

    def _d(self, v) -> Decimal:
        if v in (None, "", "null"):
            return Decimal("0")
        try:
            return Decimal(str(v))
        except Exception:
            return Decimal("0")

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        ser = self.get_serializer(qs, many=True)

        grouped = OrderedDict()

        for row in ser.data:
            # ✅ group_date: date bo‘lsa o‘sha, bo‘lmasa created_time.date()
            if row.get("date"):
                group_date = row["date"]  # YYYY-MM-DD
            else:
                ct = row.get("created_time")  # ISO datetime
                group_date = (str(ct)[:10] if ct else "no-date")

            if group_date not in grouped:
                grouped[group_date] = {
                    "date": group_date,
                    "count": 0,
                    "totals": {
                        "summa_total_dollar": "0.00",
                        "summa_dollar": "0.00",
                        "summa_naqt": "0.00",
                        "summa_kilik": "0.00",
                        "summa_terminal": "0.00",
                        "summa_transfer": "0.00",
                        "discount_amount": "0.00",
                    },
                    "items": []
                }

            g = grouped[group_date]
            g["items"].append(row)
            g["count"] += 1

            t = g["totals"]
            t["summa_total_dollar"] = str(self._d(t["summa_total_dollar"]) + self._d(row.get("summa_total_dollar")))
            t["summa_dollar"] = str(self._d(t["summa_dollar"]) + self._d(row.get("summa_dollar")))
            t["summa_naqt"] = str(self._d(t["summa_naqt"]) + self._d(row.get("summa_naqt")))
            t["summa_kilik"] = str(self._d(t["summa_kilik"]) + self._d(row.get("summa_kilik")))
            t["summa_terminal"] = str(self._d(t["summa_terminal"]) + self._d(row.get("summa_terminal")))
            t["summa_transfer"] = str(self._d(t["summa_transfer"]) + self._d(row.get("summa_transfer")))
            t["discount_amount"] = str(self._d(t["discount_amount"]) + self._d(row.get("discount_amount")))

        # ✅ 2 xonali format
        for g in grouped.values():
            for k, v in g["totals"].items():
                g["totals"][k] = f"{self._d(v):.2f}"

        # ✅ grouped date larni yangi -> eski qilib chiqarish (ixtiyoriy, odatda kerak)
        results = list(grouped.values())
        results.sort(key=lambda x: x["date"], reverse=True)

        return Response(results)


class VozvratOrderView(ListCreateAPIView):
    serializer_class = VozvratOrderListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            VozvratOrder.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'client', 'employee', 'created_by')
            .order_by('pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = VozvratOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # requestda filial kelgan bo'lsa olamiz, bo'lmasa user.order_filial
        filial = serializer.validated_data.get('filial') or request.user.order_filial

        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # user shu filialda ishlaydimi?
        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun vozvrat order yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user, filial=filial)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VozvratOrderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = VozvratOrderSerializer

    def get_queryset(self):
        return VozvratOrder.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk)
        serializer = VozvratOrderListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk, is_delete=False)

        serializer = VozvratOrderUpdateSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class VozvratOrderReturnView(RetrieveUpdateDestroyAPIView):
    serializer_class = VozvratOrderReturnSerializer
    http_method_names = ['put']

    def put(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk, is_delete=False)

        serializer = VozvratOrderReturnSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class VozvratOrderEditView(RetrieveUpdateDestroyAPIView):
    serializer_class = VozvratOrderSerializer
    http_method_names = ['put']

    def put(self, request, pk):
        instance = get_object_or_404(VozvratOrder, id=pk, is_delete=False)

        serializer = VozvratOrderReturnSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class VozvratOrderHardDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def _d(self, v) -> Decimal:
        if v is None or v == "":
            return Decimal("0")
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    def _q2(self, v: Decimal) -> Decimal:
        return (v or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _uzs_to_usd(self, uzs: Decimal, rate: Decimal) -> Decimal:
        rate = self._d(rate)
        if rate <= 0:
            raise ValueError("exchange_rate must be > 0")
        return self._q2(self._d(uzs) / rate)

    def _calc_paid_usd(self, vo: VozvratOrder) -> Decimal:
        rate = self._d(vo.exchange_rate)
        paid = (
            self._d(vo.summa_dollar)
            + self._uzs_to_usd(self._d(vo.summa_naqt), rate)
            + self._uzs_to_usd(self._d(vo.summa_kilik), rate)
            + self._uzs_to_usd(self._d(vo.summa_terminal), rate)
            + self._uzs_to_usd(self._d(vo.summa_transfer), rate)
            - self._d(vo.discount_amount)
        )
        return self._q2(paid)

    def _calc_products_usd(self, vo: VozvratOrder) -> Decimal:
        rate = self._d(vo.exchange_rate)
        qs = OrderHistoryProduct.objects.filter(
            vozvrat_order_id=vo.id,
            is_delete=False
        )

        total = Decimal("0")
        for p in qs:
            cnt = self._d(p.count or 0)

            if p.price_dollar and self._d(p.price_dollar) > 0:
                unit_usd = self._d(p.price_dollar)
            else:
                unit_usd = self._uzs_to_usd(self._d(p.price_sum), rate)

            total += cnt * unit_usd

        return self._q2(total)

    def _effect(self, vo: VozvratOrder) -> Decimal:
        # client debtga net ta’sir
        return self._q2(self._calc_paid_usd(vo) - self._calc_products_usd(vo))

    def _reverse_stock(self, vo: VozvratOrder):
        """
        Confirm paytida stock +count bo'lgan bo'lsa,
        hard delete paytida teskari qilamiz: stock -= count
        """
        items = OrderHistoryProduct.objects.filter(
            vozvrat_order_id=vo.id,
            is_delete=False
        ).select_related("product", "sklad")

        for it in items:
            if not it.product_id:
                continue
            if not it.sklad_id:
                # sizda sklad majburiy bo'lishi kerak
                raise ValueError("OrderHistoryProduct.sklad is required for stock reversal")

            qty = int(it.count or 0)
            if qty <= 0:
                continue

            prod = Product.objects.select_for_update(of=("self",)).get(pk=it.product_id)
            stock, _ = ProductStock.objects.select_for_update().get_or_create(
                product_id=prod.pk,
                sklad_id=it.sklad_id,
                defaults={"count": 0}
            )

            cur = int(stock.count or 0)
            if cur - qty < 0:
                raise ValueError(
                    f"Stock minus bo'lib ketadi. product={prod.pk}, sklad={it.sklad_id}, ombor={cur}, ayirish={qty}"
                )

            ProductStock.objects.filter(pk=stock.pk).update(count=F("count") - qty)

            if prod.count is not None:
                curp = int(prod.count or 0)
                if curp - qty < 0:
                    raise ValueError(f"Product.count minus bo'lib ketadi. product={prod.pk}, count={curp}, ayirish={qty}")
                Product.objects.filter(pk=prod.pk).update(count=F("count") - qty)

    @transaction.atomic
    def delete(self, request, pk: int):
        vozvrat = get_object_or_404(
            VozvratOrder.objects.select_for_update(),
            pk=pk
        )

        if vozvrat.is_delete is False:
            return Response(
                {"detail": "Avval soft delete qiling (is_delete=True) keyin hard delete qilish mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Balansga ta'sir bo'lganmi?
        affected = (vozvrat.is_karzinka is False) and (vozvrat.is_vazvrat_status is True)

        if affected:
            if vozvrat.client_id is None:
                return Response({"detail": "VozvratOrder.client null. Balansni qaytarib bo'lmaydi."},
                                status=status.HTTP_400_BAD_REQUEST)

            # lock client
            client = get_object_or_404(Client.objects.select_for_update(), pk=vozvrat.client_id)

            # 1) debt reversal
            try:
                effect = self._effect(vozvrat)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # reverse: Client.total_debt -= effect
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") - effect)

            # 2) stock reversal (confirmda stock qo‘shilgan bo‘lsa)
            try:
                self._reverse_stock(vozvrat)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3) vozvratga bog'langan mahsulotlarni hard delete
        OrderHistoryProduct.objects.filter(vozvrat_order_id=vozvrat.id).delete()

        # 4) vozvrat order hard delete
        vozvrat.delete()

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)
