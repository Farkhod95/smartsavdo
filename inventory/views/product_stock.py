from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.serializer.products_stock import ProductStockListSerializer, ProductStockSerializer
from restapp.pagination import ResultsSetPagination
from inventory.filterset import ProductStockFilter
from inventory.models import ProductStock


class ProductStockFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in ProductStock._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ProductStockView(ListCreateAPIView):
    serializer_class = ProductStockListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductStockFilter
    search_fields = ()  # count integer, product/ sklad FK; kerak bo'lsa product__name qo'shamiz
    ordering = ['-pk']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductStock.objects.select_related('product', 'sklad').all()

    def post(self, request, **kwargs):
        serializer = ProductStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ProductStockDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductStock.objects.select_related('product', 'sklad').all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        obj = get_object_or_404(ProductStock, id=pk)
        serializer = ProductStockListSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = get_object_or_404(ProductStock, id=pk)
        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)
