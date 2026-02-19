from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from collections import OrderedDict
from decimal import Decimal
from django.db.models import QuerySet
from rest_framework.generics import ListAPIView

from sales.filterset import VozvratOrderFilter
from sales.models import VozvratOrder, OrderHistoryProduct, Order, Client
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.vozvrat_order import VozvratOrderSerializer, VozvratOrderListSerializer, \
    VozvratOrderUpdateSerializer


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
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-created_time', '-pk']  # ichida tartib

    def get_queryset(self):
        return VozvratOrder.objects.filter(is_delete=False).order_by('-created_time', '-pk')

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
                group_date = row["date"]  # already YYYY-MM-DD
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

        return Response(list(grouped.values()))


class VozvratOrderView(ListCreateAPIView):
    serializer_class = VozvratOrderListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = VozvratOrderFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['pk']

    def get_queryset(self):
        return VozvratOrder.objects.filter(is_delete=False)

    def post(self, request):
        serializer = VozvratOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


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


class VozvratOrderHardDeleteView(APIView):
    """
    Faqat is_delete=True bo'lgan VozvratOrder ni DB'dan butunlay o'chiradi.
    O'chirishdan oldin Order va Client balanslarini orqaga qaytaradi.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, pk: int):
        # 1) Faqat soft delete qilinganini o'chiramiz
        vozvrat = get_object_or_404(VozvratOrder.objects.select_for_update(), pk=pk)

        if vozvrat.is_delete is False:
            return Response(
                {"detail": "Avval soft delete qiling (is_delete=True) keyin hard delete qilish mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Hisob-kitoblarni qaytarish faqat is_karzinka=False bo'lsa (ya'ni balansga ta'sir qilgan bo'lsa)
        # effect = new_total_debt_client - old_total_debt_client
        # delete paytida: balanslardan effect ni AYIRAMIZ (teskari qilamiz)
        if vozvrat.is_karzinka is False:
            if vozvrat.client_id is None:
                return Response({"detail": "VozvratOrder.client null. Balansni qaytarib bo'lmaydi."},
                                status=status.HTTP_400_BAD_REQUEST)

            if vozvrat.filial_id is None:
                return Response({"detail": "VozvratOrder.filial null. Order topib bo'lmaydi."},
                                status=status.HTTP_400_BAD_REQUEST)

            client = Client.objects.select_for_update().filter(pk=vozvrat.client_id).first()
            if not client:
                return Response({"detail": "Client topilmadi."}, status=status.HTTP_404_NOT_FOUND)

            order = Order.objects.select_for_update().filter(client_id=vozvrat.client_id, filial_id=vozvrat.filial_id).first()
            if not order:
                return Response({"detail": "Order topilmadi (client+filial bo'yicha)."}, status=status.HTTP_404_NOT_FOUND)

            old_debt = vozvrat.old_total_debt_client or Decimal("0")
            new_debt = vozvrat.total_debt_client or Decimal("0")
            effect = new_debt - old_debt  # balansga qo'shilgan delta

            # Reversal (teskari)
            order.total_debt_old_client = order.total_debt_client
            order.total_debt_client = (order.total_debt_client or Decimal("0")) - effect
            order.save(update_fields=["total_debt_old_client", "total_debt_client"])

            client.total_debt = (client.total_debt or Decimal("0")) - effect
            client.save(update_fields=["total_debt"])

        # 3) Shu vozvratga bog'langan mahsulotlarni ham hard delete qilamiz
        # FK SET_NULL bo'lsa ham, “tozalash” uchun o'chirib yuboramiz
        OrderHistoryProduct.objects.filter(vozvrat_order_id=vozvrat.id).delete()

        # 4) VozvratOrder ni butunlay o'chiramiz
        vozvrat.delete()

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)