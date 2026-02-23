from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404, GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from collections import OrderedDict
from django.db.models import QuerySet
from rest_framework.generics import ListAPIView

from finance.filterset import DebtRepaymentFilter
from finance.models import DebtRepayment
from finance.serializer.debt_repayment import DebtRepaymentSerializer, DebtRepaymentListSerializer, \
    DebtRepaymentAccountingSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.models import Client


class DebtRepaymentFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in DebtRepayment._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class DebtRepaymentViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = DebtRepaymentSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return DebtRepayment.objects.filter(is_delete=False)


class DebtRepaymentGroupedByDateView(ListAPIView):
    serializer_class = DebtRepaymentListSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-date', '-pk']

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            DebtRepayment.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'client', 'employee', 'created_by')
            .order_by('-date', '-pk')
        )

    def _d(self, v) -> Decimal:
        # serializer ko‘pincha string qaytaradi, shuni Decimalga o‘tkazamiz
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
            d = row.get("date") or "no-date"

            if d not in grouped:
                grouped[d] = {
                    "date": d,
                    "count": 0,
                    "totals": {
                        "summa_total_dollar": "0.00",
                        "summa_dollar": "0.00",
                        "summa_naqt": "0.00",
                        "summa_kilik": "0.00",
                        "summa_terminal": "0.00",
                        "summa_transfer": "0.00",
                        "discount_amount": "0.00",
                        "zdacha_dollar": "0.00",
                        "zdacha_som": "0.00",
                    },
                    "items": []
                }

            g = grouped[d]
            g["items"].append(row)
            g["count"] += 1

            # yig‘indilar
            g_tot = g["totals"]
            g_tot["summa_total_dollar"] = str(self._d(g_tot["summa_total_dollar"]) + self._d(row.get("summa_total_dollar")))
            g_tot["summa_dollar"] = str(self._d(g_tot["summa_dollar"]) + self._d(row.get("summa_dollar")))
            g_tot["summa_naqt"] = str(self._d(g_tot["summa_naqt"]) + self._d(row.get("summa_naqt")))
            g_tot["summa_kilik"] = str(self._d(g_tot["summa_kilik"]) + self._d(row.get("summa_kilik")))
            g_tot["summa_terminal"] = str(self._d(g_tot["summa_terminal"]) + self._d(row.get("summa_terminal")))
            g_tot["summa_transfer"] = str(self._d(g_tot["summa_transfer"]) + self._d(row.get("summa_transfer")))
            g_tot["discount_amount"] = str(self._d(g_tot["discount_amount"]) + self._d(row.get("discount_amount")))
            g_tot["zdacha_dollar"] = str(self._d(g_tot["zdacha_dollar"]) + self._d(row.get("zdacha_dollar")))
            g_tot["zdacha_som"] = str(self._d(g_tot["zdacha_som"]) + self._d(row.get("zdacha_som")))

        # format: 2 xonali ko‘rinishda qaytaramiz
        for g in grouped.values():
            for k, v in g["totals"].items():
                g["totals"][k] = f"{self._d(v):.2f}"

        return Response(list(grouped.values()))


class DebtRepaymentView(ListCreateAPIView):
    serializer_class = DebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            DebtRepayment.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'client', 'employee', 'created_by')
            .order_by('-pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = DebtRepaymentAccountingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Accounting serializer filialni validated_data ga qo'ygan bo'lishi mumkin
        filial = serializer.validated_data.get('filial') or request.user.order_filial

        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun qarz to‘lovi qilish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user, filial=filial)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DebtRepaymentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentAccountingSerializer

    def get_queryset(self):
        return DebtRepayment.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        serializer = DebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk, is_delete=False)

        serializer = DebtRepaymentAccountingSerializer(
            instance,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        """
        Soft delete:
        - Agar debt_status True bo'lsa rollback (client debtga pulni qaytarib qo'yadi)
        - keyin is_delete=True
        """
        dr = get_object_or_404(
            DebtRepayment.objects.select_for_update(of=("self",)),
            id=pk,
            is_delete=False
        )

        # rollback if confirmed
        if dr.debt_status and dr.client_id:
            client = Client.objects.select_for_update().get(pk=dr.client_id)
            old_paid = dr.summa_total_dollar or Decimal("0")

            # debt back
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + old_paid)

        dr.is_delete = True
        dr.save(update_fields=["is_delete", "updated_time"])

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)



class DebtRepaymentKarzinkaView(ListCreateAPIView):
    serializer_class = DebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = DebtRepaymentFilter
    search_fields = ('client__full_name', 'employee__username', 'note')
    ordering = ['-pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            DebtRepayment.objects
            .filter(is_delete=True, filial_id__in=user_filial_ids)
            .select_related('filial', 'client', 'employee', 'created_by')
            .order_by('-pk')
        )


class DebtRepaymentRestoreKarzinkaView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DebtRepaymentSerializer  # sizda qaysi serializer bo'lsa shuni qo'ying
    http_method_names = ['put']

    @transaction.atomic
    def put(self, request, pk: int):
        user = request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        dr = get_object_or_404(
            DebtRepayment.objects.select_for_update().select_related('client', 'filial'),
            pk=pk,
            is_delete=True,
            filial_id__in=user_filial_ids
        )

        # ixtiyoriy: tasdiqlangan (posted) bo'lsa restore qilishni taqiqlash
        # agar sizda mantiq shunaqa bo'lsa yoqing, bo'lmasa olib tashlang
        # if dr.debt_status:
        #     return Response(
        #         {"detail": "Tasdiqlangan (debt_status=True) to'lovni karzinkadan restore qilib bo'lmaydi."},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        dr.is_delete = False
        dr.save(update_fields=['is_delete'])

        return Response(self.get_serializer(dr).data, status=status.HTTP_200_OK)


class DebtRepaymentDetailKarzinkaView(RetrieveUpdateDestroyAPIView):
    serializer_class = DebtRepaymentSerializer
    http_method_names = ['delete', 'get']

    def get_queryset(self):
        return DebtRepayment.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(DebtRepayment, id=pk)
        serializer = DebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, pk):
        dr = get_object_or_404(
            DebtRepayment.objects.select_for_update(of=("self",)),
            id=pk
        )

        if dr.debt_status and dr.client_id:
            client = Client.objects.select_for_update().get(pk=dr.client_id)
            old_paid = dr.summa_total_dollar or Decimal("0")
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + old_paid)

        dr.delete()
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)