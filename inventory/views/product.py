from django.db.models import Exists, OuterRef, Prefetch
from django.db.models import Q
from collections import OrderedDict
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
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductFilter
    search_fields = ('branch__name', 'model__name', 'type__name', "size__size")
    ordering = ['pk']
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        images_qs = ProductImage.objects.only('id', 'product_id', 'file').order_by('id')

        qs = (
            Product.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'branch', 'branch_category', 'model', 'type', 'size')
            .prefetch_related(Prefetch('images', queryset=images_qs))  # hammasi keladi, lekin serializer 1 tasini chiqaradi
        )
        return qs

    def create(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # requestda filial kelgan bo'lsa olamiz, bo'lmasa user.order_filial
        filial = serializer.validated_data.get('filial') or request.user.order_filial

        if filial is None:
            return Response(
                {"filial": "filial yuborilmadi va userda order_filial ham yo‘q."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # user shu filialda ishlaydimi?
        if not request.user.filials.filter(id=filial.id).exists():
            return Response(
                {"detail": "Sizda bu filial uchun product yaratish huquqi yo‘q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer.save(created_by=request.user, filial=filial)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductGroupByModelList(ListCreateAPIView):
    serializer_class = ProductListOneImageSerializer
    pagination_class = ResultsSetPagination
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductFilter
    search_fields = ('filial__name', 'branch__name', 'model__name', 'type__name', "size__name")
    ordering = ['pk']
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        user_filial_ids = user.filials.values_list('id', flat=True)

        images_qs = ProductImage.objects.only('id', 'product_id', 'file').order_by('id')

        qs = (
            Product.objects
            .filter(is_delete=False, filial_id__in=user_filial_ids)
            .select_related('filial', 'branch', 'branch_category', 'model', 'type', 'size')
            .prefetch_related(Prefetch('images', queryset=images_qs))
        )
        return qs

    # ✅ GET ni gruppalab chiqarish (queryset logikasi o'zgarmaydi)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is None:
            # pagination yo'q bo'lsa ham ishlaydi
            serializer = self.get_serializer(queryset, many=True)
            grouped = self._group_by_model(serializer.data)
            return Response(grouped)

        serializer = self.get_serializer(page, many=True)
        grouped = self._group_by_model(serializer.data)

        # paginator count/next/prev saqlanadi, faqat results = grouped bo'ladi
        return self.get_paginated_response(grouped)

    def _group_by_model(self, items):
        """
        items: ProductListOneImageSerializer.data (list)
        return: [
          {
            "model": <id or None>,
            "model_detail": {...} or None,
            "total_count": <sum count>,
            "items": [ ...products... ]
          },
          ...
        ]
        """
        buckets = OrderedDict()

        for p in items:
            model_id = p.get('model')  # FK id
            key = model_id if model_id is not None else 'no-model'

            if key not in buckets:
                buckets[key] = {
                    "model": model_id,
                    "model_detail": p.get('model_detail'),
                    "total_product_count": 0,
                    "items": []
                }

            # count null bo'lishi mumkin
            c = p.get('count')
            try:
                c_int = int(c) if c is not None else 0
            except (TypeError, ValueError):
                c_int = 0

            buckets[key]["total_product_count"] += c_int
            buckets[key]["items"].append(p)

        return list(buckets.values())



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
