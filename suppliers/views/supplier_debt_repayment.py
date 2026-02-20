from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from suppliers.filterset import SupplierDebtRepaymentFilter
from suppliers.models import SupplierDebtRepayment
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.serializer.supplier_debt_repayment import SupplierDebtRepaymentSerializer, \
    SupplierDebtRepaymentListSerializer


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


class SupplierDebtRepaymentView(ListCreateAPIView):
    serializer_class = SupplierDebtRepaymentListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierDebtRepaymentFilter
    search_fields = ('supplier__name', 'employee__username')
    ordering = ['pk']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            SupplierDebtRepayment.objects
            .filter(supplier__isnull=False, supplier__filial_id__in=user_filial_ids)
            .select_related('supplier', 'supplier__filial', 'employee')
            .order_by('pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = SupplierDebtRepaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # (tavsiya) user o'zi ishlaydigan filialdagi supplier uchun to'lov qilyaptimi - tekshiruv
        supplier = serializer.validated_data.get('supplier')
        if supplier and supplier.filial_id:
            if not request.user.filials.filter(id=supplier.filial_id).exists():
                return Response(
                    {"detail": "Sizda bu supplier (filial) bo‘yicha to‘lov qilish huquqi yo‘q."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierDebtRepaymentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierDebtRepaymentSerializer

    def get_queryset(self):
        return SupplierDebtRepayment.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(SupplierDebtRepayment, id=pk)
        serializer = SupplierDebtRepaymentListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(SupplierDebtRepayment, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(SupplierDebtRepayment, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
