from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from django.utils import timezone
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from django.db import transaction

from suppliers.filterset import SupplierDebtRepaymentFilter
from suppliers.models import SupplierDebtRepayment, Supplier, SupplierAccount
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.serializer.supplier_debt_repayment import SupplierDebtRepaymentSerializer, \
    SupplierDebtRepaymentListSerializer, SupplierDebtRepaymentPostSerializer
from suppliers.services.supplier_debt_repayment import update_supplier_debt_repayment, \
    delete_supplier_debt_repayment


class SupplierDebtRepaymentFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in SupplierDebtRepayment._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class SupplierDebtRepaymentViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = SupplierDebtRepaymentSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierDebtRepaymentFilter
    search_fields = ('supplier__name', 'employee__username')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return SupplierDebtRepayment.objects.all()


def _d(val) -> Decimal:
    try:
        return Decimal(val or 0)
    except Exception:
        return Decimal("0")


class SupplierDebtRepaymentView(ListCreateAPIView):
    serializer_class = SupplierDebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierDebtRepaymentFilter
    search_fields = ('supplier__name', 'employee__full_name')
    ordering = ['-date', '-pk']  # ✅ tavsiya: eng yangi to'lovlar tepada

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            SupplierDebtRepayment.objects
            .filter(supplier__isnull=False, supplier__filial_id__in=user_filial_ids)
            .select_related('supplier', 'supplier__filial', 'employee')
            .order_by('-date', '-pk')
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = SupplierDebtRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supplier: Supplier = serializer.validated_data.get('supplier')
        if not supplier:
            return Response({"supplier": "Supplier majburiy."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ user faqat o'z filialidagi supplier uchun to'lov qilsin
        if supplier.filial_id and not request.user.filials.filter(id=supplier.filial_id).exists():
            return Response(
                {"detail": "Sizda bu supplier (filial) bo‘yicha to‘lov qilish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        # to'lov summasi
        paid_total = _d(serializer.validated_data.get('summa_total_dollar')).quantize(Decimal("0.01"))

        # SupplierAccount lock
        account, _ = SupplierAccount.objects.select_for_update().get_or_create(
            supplier_id=supplier.id,
            defaults={"total_turnover": 0, "filial_debt": 0},
        )

        old_debt = _d(account.filial_debt).quantize(Decimal("0.01"))

        # ✅ 1) agar qarzdan ko'p to'lamasin (AVANS yo'q deb qabul qilyapman)
        if paid_total > old_debt:
            return Response(
                {"summa_total_dollar": f"To‘lov ({paid_total}) qarzdan ({old_debt}) katta bo‘lishi mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_debt = (old_debt - paid_total).quantize(Decimal("0.01"))

        # ✅ 2) SupplierAccount yangilash
        account.filial_debt = new_debt
        account.save(update_fields=["filial_debt"])

        # ✅ 3) SupplierDebtRepayment yaratish
        repayment = SupplierDebtRepayment.objects.create(
            supplier_id=supplier.id,
            employee=request.user,
            date=serializer.validated_data.get('date') or timezone.localdate(),

            total_debt_old=old_debt,
            total_debt=new_debt,

            summa_total_dollar=paid_total,
            summa_dollar=_d(serializer.validated_data.get('summa_dollar')).quantize(Decimal("0.01")),
            summa_naqt=_d(serializer.validated_data.get('summa_naqt')).quantize(Decimal("0.01")),
            summa_kilik=_d(serializer.validated_data.get('summa_kilik')).quantize(Decimal("0.01")),
            summa_terminal=_d(serializer.validated_data.get('summa_terminal')).quantize(Decimal("0.01")),
            summa_transfer=_d(serializer.validated_data.get('summa_transfer')).quantize(Decimal("0.01")),

            created_by=request.user,
        )

        out = SupplierDebtRepaymentListSerializer(repayment).data
        return Response(out, status=status.HTTP_201_CREATED)


class SupplierDebtRepaymentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierDebtRepaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # xavfsizlik: user faqat o'z filialidagi supplier repaymentlarini ko'rsin
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)
        return SupplierDebtRepayment.objects.filter(supplier__filial_id__in=user_filial_ids)

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = SupplierDebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated = update_supplier_debt_repayment(
                repayment_id=instance.id,
                validated_data=serializer.validated_data,
                user=request.user
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        out = SupplierDebtRepaymentListSerializer(updated).data
        return Response(out, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        result = delete_supplier_debt_repayment(repayment_id=instance.id, user=request.user)

        # 204 ham bo'ladi, lekin debugging uchun xohlasangiz 200 qaytaring:
        # return Response(result, status=status.HTTP_200_OK)

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)
