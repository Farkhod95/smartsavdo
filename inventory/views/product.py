from django.db.models import Exists, OuterRef, Prefetch, Subquery, Min
from django.contrib.postgres.aggregates import ArrayAgg

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404, ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Filial
from inventory.filterset import ProductFilter
from inventory.models import Product, ProductImage, ProductBranch, ProductBranchCategory, ProductModel, ProductType, \
    ProductTypeSize
from inventory.serializer.product import ProductListSerializer, ProductSerializer, ProductListOneImageSerializer, \
    ProductImagePublicSerializer, ProductPublicGroupedSerializer
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


class ProductPublicGroupedView(ListAPIView):
    """
    /product/public — GROUPED:
    (filial, branch, branch_category, model, type) bo‘yicha bitta qator,
    ichida sizes[] ro‘yxati, node matni va (xohlasa) bitta image.
    """
    permission_classes = (AllowAny,)
    pagination_class = ResultsSetPagination
    serializer_class = ProductPublicGroupedSerializer

    # ❗ OrderingFilter ni olib tashlaymiz (has_image Product’da yo‘q!)
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = ProductFilter
    search_fields = ('note', 'filial__name', 'branch__name', 'model__name', 'type__name')

    http_method_names = ['get']

    def get_base_queryset(self):
        return Product.objects.filter(is_delete=False)

    def _group_queryset(self, base_qs):
        """
        base_qs (Product queryset) ustida GROUP BY qilib dict queryset qaytaradi.
        """
        # Group bo‘yicha "hech bo‘lmasa bitta rasm bormi?"
        has_image_subq = ProductImage.objects.filter(
            product__is_delete=False,
            product__filial_id=OuterRef('filial_id'),
            product__branch_id=OuterRef('branch_id'),
            product__branch_category_id=OuterRef('branch_category_id'),
            product__model_id=OuterRef('model_id'),
            product__type_id=OuterRef('type_id'),
        )

        # Group bo‘yicha birinchi rasm (file) (id bo‘yicha)
        first_image_subq = ProductImage.objects.filter(
            product__is_delete=False,
            product__filial_id=OuterRef('filial_id'),
            product__branch_id=OuterRef('branch_id'),
            product__branch_category_id=OuterRef('branch_category_id'),
            product__model_id=OuterRef('model_id'),
            product__type_id=OuterRef('type_id'),
        ).order_by('id').values('file')[:1]

        grouped = (
            base_qs
            .values('filial_id', 'branch_id', 'branch_category_id', 'model_id', 'type_id')
            .annotate(
                min_pk=Min('pk'),
                size_ids=ArrayAgg('size_id', distinct=True, filter=Q(size_id__isnull=False)),
                has_image=Exists(has_image_subq),
                first_image=Subquery(first_image_subq),
            )
        )
        return grouped

    def _apply_ordering(self, grouped_qs):
        """
        ordering query param: ?ordering=-has_image,min_pk
        Ruxsat etilgan: has_image, min_pk
        """
        ordering_param = self.request.query_params.get('ordering')

        allowed = {'has_image', 'min_pk'}

        if not ordering_param:
            return grouped_qs.order_by('-has_image', 'min_pk')

        parts = [p.strip() for p in ordering_param.split(',') if p.strip()]
        order_fields = []

        for p in parts:
            desc = p.startswith('-')
            field = p[1:] if desc else p
            if field not in allowed:
                continue
            order_fields.append(f"-{field}" if desc else field)

        if not order_fields:
            order_fields = ['-has_image', 'min_pk']

        return grouped_qs.order_by(*order_fields)

    def list(self, request, *args, **kwargs):
        # 1) Search + Filter avval Product ustida ishlaydi (tez)
        base_qs = self.get_base_queryset()
        base_qs = self.filter_queryset(base_qs)

        # 2) Group
        grouped_qs = self._group_queryset(base_qs)

        # 3) Ordering endi annotate bo‘lgan grouped_qs’da bajariladi ✅
        grouped_qs = self._apply_ordering(grouped_qs)

        # 4) Pagination (group bo‘yicha)
        page = self.paginate_queryset(grouped_qs)
        rows = list(page) if page is not None else list(grouped_qs)

        # 5) Bulk detail maps (N+1 bo‘lmasin)
        filial_ids = {x['filial_id'] for x in rows if x.get('filial_id')}
        branch_ids = {x['branch_id'] for x in rows if x.get('branch_id')}
        branch_category_ids = {x['branch_category_id'] for x in rows if x.get('branch_category_id')}
        model_ids = {x['model_id'] for x in rows if x.get('model_id')}
        type_ids = {x['type_id'] for x in rows if x.get('type_id')}

        size_ids = set()
        for x in rows:
            for sid in (x.get('size_ids') or []):
                if sid:
                    size_ids.add(sid)

        filial_map = Filial.objects.in_bulk(filial_ids)
        branch_map = ProductBranch.objects.in_bulk(branch_ids)
        branch_category_map = ProductBranchCategory.objects.in_bulk(branch_category_ids)
        model_map = ProductModel.objects.in_bulk(model_ids)
        type_map = ProductType.objects.in_bulk(type_ids)

        size_map = {
            s.id: s for s in ProductTypeSize.objects.select_related('unit', 'product_type').filter(id__in=size_ids)
        }

        # 6) Serializer input
        payload = [
            {
                "filial": x["filial_id"],
                "branch": x["branch_id"],
                "branch_category": x["branch_category_id"],
                "model": x["model_id"],
                "type": x["type_id"],
                "min_pk": x["min_pk"],
                "size_ids": x.get("size_ids") or [],
                "has_image": bool(x.get("has_image")),
                "first_image": x.get("first_image"),
            }
            for x in rows
        ]

        ser = self.get_serializer(
            payload,
            many=True,
            context={
                "request": request,
                "filial_map": filial_map,
                "branch_map": branch_map,
                "branch_category_map": branch_category_map,
                "model_map": model_map,
                "type_map": type_map,
                "size_map": size_map,
            }
        )

        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)


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
            .filter(is_delete=False)
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
