from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from suppliers.filterset import SupplierFilter
from suppliers.models import Supplier
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.serializer.supplier import SupplierSerializer, SupplierListSerializer


class SupplierFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

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
    Public list (faqat GET), DistrictViewList kabi.
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
        return Supplier.objects.filter(is_delete=False, is_active=True)


class SupplierView(ListCreateAPIView):
    serializer_class = SupplierListSerializer
    pagination_class = ResultsSetPagination

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = SupplierFilter
    search_fields = ('name', 'inn', 'address')
    ordering = ['pk']

    def get_queryset(self):
        user = self.request.user

        # userga tegishli filiallar
        user_filial_ids = user.filials.values_list('id', flat=True)

        return (
            Supplier.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'region', 'district')
            .order_by('pk')
        )

    def post(self, request, *args, **kwargs):
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # (ixtiyoriy, lekin tavsiya) user o'zi ishlaydigan filialga supplier qo'shayotganini tekshirish
        filial_id = serializer.validated_data.get('filial').id if serializer.validated_data.get('filial') else None
        if filial_id and not request.user.filials.filter(id=filial_id).exists():
            return Response(
                {"detail": "Sizda bu filialga supplier qo‘shish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierSerializer

    def get_queryset(self):
        return Supplier.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Supplier, id=pk)
        serializer = SupplierListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Supplier, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Supplier, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
