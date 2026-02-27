from django.db.models import OuterRef, Subquery, DecimalField, Value
from django.db.models.functions import Coalesce
from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from suppliers.filterset import SupplierFilter
from suppliers.models import Supplier, SupplierAccount
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent

from suppliers.serializer.supplier import SupplierSerializer, SupplierListSerializer


# ---------------------------
# ✅ Helper: debt annotate
# ---------------------------
def annotate_supplier_debt(qs):
    debt_subq = (
        SupplierAccount.objects
        .filter(supplier_id=OuterRef('pk'))
        .values('filial_debt')[:1]
    )

    debt_field = DecimalField(max_digits=20, decimal_places=2)

    return qs.annotate(
        filial_debt_db=Coalesce(
            Subquery(debt_subq, output_field=debt_field),
            Value(Decimal('0.00'), output_field=debt_field),  # ✅ MUHIM: output_field!
            output_field=debt_field,  # ✅ MUHIM: Coalesce ham bir xil type qaytarsin
        )
    )


class SupplierFieldInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        field_info = []
        for field in Supplier._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class SupplierViewList(ListCreateAPIView):
    """
    Public list (faqat GET)
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = SupplierSerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierFilter
    search_fields = ('name', 'inn', 'address')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        qs = Supplier.objects.filter(is_delete=False, is_active=True)
        qs = annotate_supplier_debt(qs)
        return qs.order_by('pk')


class SupplierView(ListCreateAPIView):
    """
    Private list/create (login shart)
    """
    serializer_class = SupplierListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = (IsAuthenticated,)

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierFilter
    search_fields = ('name', 'inn', 'address')
    ordering = ['pk']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        qs = (
            Supplier.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'region', 'district')
        )
        qs = annotate_supplier_debt(qs)
        return qs.order_by('pk')

    def post(self, request, *args, **kwargs):
        # create uchun oddiy SupplierSerializer ishlatyapmiz (detail serializer)
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filial = serializer.validated_data.get('filial')
        filial_id = filial.id if filial else None

        # ✅ user faqat o'z filialiga supplier qo'shsin
        if filial_id and not request.user.filials.filter(id=filial_id).exists():
            return Response(
                {"detail": "Sizda bu filialga supplier qo‘shish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        obj = serializer.save(created_by=request.user)

        # response ni list serializer bilan qaytaramiz (detail+debt ko‘rinsin)
        # annotate kerak (filial_debt_db bo‘lishi uchun)
        obj_qs = annotate_supplier_debt(
            Supplier.objects.filter(pk=obj.pk).select_related('filial', 'region', 'district')
        )
        obj2 = obj_qs.first()

        out = SupplierListSerializer(obj2).data
        return Response(out, status=status.HTTP_201_CREATED)


class SupplierDetailView(RetrieveUpdateDestroyAPIView):
    """
    Private detail (login shart) + filial bo‘yicha access control 100% ishlaydi.
    """
    serializer_class = SupplierSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user_filial_ids = self.request.user.filials.values_list('id', flat=True)

        qs = (
            Supplier.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'region', 'district')
        )
        qs = annotate_supplier_debt(qs)
        return qs

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = SupplierListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ filialni o‘zgartirishsa ham userga tegishli filial bo‘lishi shart
        filial = serializer.validated_data.get('filial')
        filial_id = filial.id if filial else None
        if filial_id and not request.user.filials.filter(id=filial_id).exists():
            return Response(
                {"detail": "Sizda bu filialga supplierni o‘tkazish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        obj = serializer.save(updated_by=request.user)

        # annotate bilan qaytaramiz
        obj_qs = annotate_supplier_debt(
            Supplier.objects.filter(pk=obj.pk).select_related('filial', 'region', 'district')
        )
        obj2 = obj_qs.first()
        out = SupplierListSerializer(obj2).data
        return Response(out, status=status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)

        # Siz hozir soft delete qilyapsiz (is_delete=True) — shuni qoldirdim
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)