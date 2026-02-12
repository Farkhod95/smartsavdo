from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.filterset import ProductHistoryFilter
from inventory.models import ProductHistory
from inventory.serializer.product_history import ProductHistoryListSerializer, ProductHistorySerializer, ProductHistoryCreateSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ProductHistoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in ProductHistory._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ProductHistoryViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ProductHistorySerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductHistoryFilter
    search_fields = ('note', 'product__id', 'purchase_invoice__id', 'branch__name', 'model__name', 'type__name')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return ProductHistory.objects.all()


class ProductHistoryView(ListCreateAPIView):
    serializer_class = ProductHistoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductHistoryFilter
    search_fields = ('note', 'product__id', 'purchase_invoice__id', 'branch__name', 'model__name', 'type__name')
    ordering = ['-pk']

    def get_queryset(self):
        return ProductHistory.objects.all()
    #
    # def perform_create(self, serializer):
    #     # BaseModel’da created_by bo‘lsa shu yerda berib yuboramiz
    #     serializer.save(created_by=self.request.user)
    def post(self, request):
        serializer = ProductHistoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ProductHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductHistorySerializer

    def get_queryset(self):
        return ProductHistory.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ProductHistory, id=pk)
        serializer = ProductHistoryListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ProductHistory, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(ProductHistory, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
