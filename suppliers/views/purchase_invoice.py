from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from suppliers.filterset import PurchaseInvoiceFilter
from suppliers.models import PurchaseInvoice
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.serializer.purchase_invoice import PurchaseInvoiceSerializer, PurchaseInvoiceListSerializer


class PurchaseInvoiceFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in PurchaseInvoice._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class PurchaseInvoiceViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = PurchaseInvoiceSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = PurchaseInvoiceFilter
    search_fields = ('supplier__name', 'filial__name', 'sklad__name', 'employee__username')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return PurchaseInvoice.objects.all()


class PurchaseInvoiceView(ListCreateAPIView):
    serializer_class = PurchaseInvoiceListSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = PurchaseInvoiceFilter
    search_fields = ('supplier__name', 'filial__name', 'sklad__name', 'employee__username')
    ordering = ['pk']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            PurchaseInvoice.objects
            .filter(filial_id__in=user_filial_ids)
            .select_related('supplier', 'filial', 'sklad', 'employee')
            .order_by('pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = PurchaseInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # (tavsiya) user faqat o'z filialiga invoice yaratsin
        filial = serializer.validated_data.get('filial')
        if filial and not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun faktura yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        # (ixtiyoriy) sklad ham filialga tegishli bo'lsa, tekshiruv:
        sklad = serializer.validated_data.get('sklad')
        if sklad and hasattr(sklad, 'filial_id') and filial and sklad.filial_id != filial.id:
            return Response(
                {"detail": "Tanlangan sklad bu filialga tegishli emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PurchaseInvoiceDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = PurchaseInvoiceSerializer

    def get_queryset(self):
        return PurchaseInvoice.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(PurchaseInvoice, id=pk)
        serializer = PurchaseInvoiceListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(PurchaseInvoice, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(PurchaseInvoice, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
