from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from smartsavdo.filterset import ProductImageFilter
from smartsavdo.models import ProductImage
from smartsavdo.serializers import ProductImageSerializer, ProductImageListSerializer

from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ProductImageFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []

        for field in ProductImage._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })

        return Response(field_info)


class ProductImageViewList(ListCreateAPIView):
    serializer_class = ProductImageListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    search_fields = ('product__name', 'product__category__name', 'product__model__name', 'product__model_type__name')
    permission_classes = (AllowAny,)
    ordering_fields = ('id', 'created_time', 'updated_time')
    ordering = ('-id',)
    http_method_names = ['get']

    def get_queryset(self):
        return ProductImage.objects.select_related(
            'product',
            'product__category',
            'product__model',
            'product__model_type',
        ).all()

class ProductImageView(ListCreateAPIView):
    serializer_class = ProductImageListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductImageFilter
    search_fields = ('product__name', 'product__category__name', 'product__model__name', 'product__model_type__name')
    ordering_fields = ('id', 'created_time', 'updated_time')
    ordering = ('-id',)

    def get_queryset(self):
        return ProductImage.objects.select_related(
            'product',
            'product__category',
            'product__model',
            'product__model_type',
        ).all()

    def post(self, request):
        serializer = ProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ProductImageDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductImageSerializer

    def get_queryset(self):
        return ProductImage.objects.select_related(
            'product',
            'product__category',
            'product__model',
            'product__model_type',
        ).all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ProductImage, id=pk)
        serializer = ProductImageListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ProductImage, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(ProductImage, id=pk)
        instance.delete()
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)



