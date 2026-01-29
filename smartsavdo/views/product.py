from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from smartsavdo.filterset import ProductFilter
from smartsavdo.models import Product
from smartsavdo.serializers import ProductSerializer, ProductListSerializer

from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ProductFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in Product._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class ProductViewList(ListCreateAPIView):
    serializer_class = ProductListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    search_fields = (
        'category__name',
        'model__name',
        'model_type__name',
        'type',
    )
    filterset_class = ProductFilter
    permission_classes = (AllowAny,)
    ordering_fields = ('id', 'created_time', 'updated_time', 'sorting', 'price', 'real_price', 'count')
    ordering = ('-id',)
    http_method_names = ['get']

    def get_queryset(self):
        return Product.objects.select_related(
            'category',
            'model',
            'model_type',
        ).all()


class ProductView(ListCreateAPIView):
    serializer_class = ProductListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductFilter
    search_fields = ('name', 'sorting')
    ordering_fields = ('id', 'created_time', 'updated_time', 'sorting', 'price', 'real_price', 'count')
    ordering = ('-id',)

    def get_queryset(self):
        return Product.objects.select_related(
            'category',
            'model',
            'model_type',
        ).all()

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.select_related(
            'category',
            'model',
            'model_type',
        ).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(Product, id=pk)
        serializer = ProductListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(Product, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(Product, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)



