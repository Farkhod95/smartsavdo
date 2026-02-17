from django.db.models import Exists, OuterRef, Prefetch
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.filterset import ProductFilter
from inventory.models import Product, ProductImage
from inventory.serializer.product import ProductListSerializer, ProductSerializer, ProductListOneImageSerializer, \
    ProductImagePublicSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ProductFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

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
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    # authentication_classes = []
    pagination_class = ResultsSetPagination
    serializer_class = ProductListOneImageSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductFilter
    search_fields = ('note', 'filial__name', 'branch__name', 'model__name', 'type__name', "size__name")
    ordering = ['-has_image', 'pk']
    http_method_names = ['get']
    # pagination_class = None

    def get_queryset(self):
        images_qs = ProductImage.objects.only('id', 'product_id', 'file').order_by('id')

        has_image_subq = ProductImage.objects.filter(product_id=OuterRef('pk'))

        qs = (
            Product.objects
            .filter(is_delete=False, is_active=True)
            .annotate(has_image=Exists(has_image_subq))
            .select_related('filial', 'branch', 'branch_category', 'model', 'type', 'size')
            .prefetch_related(Prefetch('images', queryset=images_qs))  # hammasi keladi, lekin serializer 1 tasini chiqaradi
            .order_by('-has_image', 'pk')   # rasmli tepada, rasmsiz oxirida
        )
        return qs


class ProductView(ListCreateAPIView):
    serializer_class = ProductListOneImageSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductFilter
    search_fields = ('filial__name', 'branch__name', 'model__name', 'type__name', "size__name")
    ordering = ['pk']

    def get_queryset(self):
        images_qs = ProductImage.objects.only('id', 'product_id', 'file').order_by('id')

        qs = (
            Product.objects
            .filter(is_delete=False)
            .select_related('filial', 'branch', 'branch_category', 'model', 'type', 'size')
            .prefetch_related(Prefetch('images', queryset=images_qs))  # hammasi keladi, lekin serializer 1 tasini chiqaradi
        )
        return qs

    def create(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.all()

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
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)


class ProductAttachmentsViewList(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ProductImagePublicSerializer
    pagination_class = None  # kerak bo'lsa pagination qo'yasiz

    def get_queryset(self):
        product_id = self.kwargs.get("pk")

        # Product mavjudligini tekshirish + is_delete=False
        get_object_or_404(Product, pk=product_id)

        # Shu product'ga tegishli fayllar
        return (
            ProductImage.objects
            .filter(product_id=product_id)
            .exclude(Q(file__isnull=True) | Q(file=""))
            .order_by("id")
        )
