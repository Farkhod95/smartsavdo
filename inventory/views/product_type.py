from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404, GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.filterset import ProductTypeFilter
from inventory.models import ProductType, ProductTypeSize
from inventory.serializer.product_type import ProductTypeListSerializer, ProductTypeSerializer, ProductTypeCreateItemSerializer, \
    ProductTypeBulkCreateSerializer, ProductTypeBulkCreateResponseSerializer, ProductTypeOutSerializer, \
    ProductTypeUpdateSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ProductTypeFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in ProductType._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ProductTypeViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ProductTypeSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductTypeFilter
    search_fields = ('name', 'branch__name', 'branch_category__name', 'madel__name')
    ordering = ['sorting', '-id']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return ProductType.objects.filter(is_delete=False)


class ProductTypeView(ListCreateAPIView):
    serializer_class = ProductTypeListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductTypeFilter
    search_fields = ('name', 'branch__name', 'branch_category__name', 'madel__name')
    ordering = ['sorting', '-id']

    def get_queryset(self):
        return ProductType.objects.filter(is_delete=False)

    def post(self, request):
        serializer = ProductTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


# class ProductTypeDetailView(RetrieveUpdateDestroyAPIView):
#     serializer_class = ProductTypeSerializer
#
#     def get_queryset(self):
#         return ProductType.objects.all()
#
#     def perform_update(self, serializer):
#         serializer.save(updated_by=self.request.user)
#
#     def get(self, request, pk):
#         instance = get_object_or_404(ProductType, id=pk)
#         serializer = ProductTypeListSerializer(instance)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     def put(self, request, pk):
#         instance = get_object_or_404(ProductType, id=pk)
#         serializer = self.serializer_class(instance, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(updated_by=self.request.user)
#         return Response(serializer.data, status.HTTP_202_ACCEPTED)
#
#     def delete(self, request, pk):
#         # instance = get_object_or_404(ProductType, id=pk, is_delete=False)
#         #
#         # # 1) ProductTypeSize larni soft delete
#         # ProductTypeSize.objects.filter(product_type=instance, is_delete=False).update(is_delete=True)
#         #
#         # # 2) ProductType ni soft delete
#         # instance.is_delete = True
#         # instance.save(update_fields=['is_delete'])
#
#         instance = get_object_or_404(ProductType, id=pk)
#         ProductTypeSize.objects.filter(product_type=instance).delete()
#         instance.delete()
#         return Response(nonContent(), status.HTTP_204_NO_CONTENT)
class ProductTypeDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET  /product-type/<id>  -> [ { ... } ] format
    PUT  /product-type/<id>  -> ProductType + sizes sync
    DELETE /product-type/<id> -> ProductTypeSize delete + ProductType delete
    """
    serializer_class = ProductTypeSerializer

    def get_queryset(self):
        return ProductType.objects.all()

    def get(self, request, pk):
        instance = get_object_or_404(ProductType, id=pk)
        serializer = ProductTypeOutSerializer(instance, context={"request": request})
        # front siz so‘raganidek LIST ko‘rinishida qaytaramiz:
        return Response([serializer.data], status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ProductType, id=pk)

        serializer = ProductTypeUpdateSerializer(
            instance,
            data=request.data,
            partial=False,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)

        # update dan keyin ham frontga GET formatda qaytaramiz:
        out = ProductTypeOutSerializer(instance, context={"request": request}).data
        return Response([out], status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        instance = get_object_or_404(ProductType, id=pk)
        ProductTypeSize.objects.filter(product_type=instance).delete()
        instance.delete()
        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)


class ProductTypeCreateView(GenericAPIView):
    """
    POST /product-type/create
    Body:
    [
      {
        "madel": 1,
        "name": "Piyola",
        "sorting": 1,
        "product_type_size": [
          {"size": 12, "unit": 3},
          {"size": 64, "unit": 3}
        ]
      }
    ]
    """
    serializer_class = ProductTypeCreateItemSerializer  # item serializer

    def post(self, request, *args, **kwargs):
        # many=True -> list payload
        serializer = ProductTypeCreateItemSerializer(
            data=request.data,
            many=True,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        # Bulk create (transaction ichida)
        # DRF many=True bo‘lganda serializer.save() -> ListSerializer.create ishlaydi
        # Bizning custom ListSerializer ishlashi uchun:
        # 1) Serializer class Meta.list_serializer_class berish yoki
        # 2) pastdagi kabi qo‘lda ListSerializer ishlatish
        #
        # Eng to‘g‘risi: qo‘lda ListSerializer ishlatamiz:
        bulk = ProductTypeBulkCreateSerializer(child=ProductTypeCreateItemSerializer())
        created_objs = bulk.create(serializer.validated_data)

        # Javob: created ProductType larni size’lari bilan qaytarish
        # N+1 bo‘lmasligi uchun prefetch qilamiz
        ids = [obj.id for obj in created_objs]
        qs = ProductType.objects.filter(id__in=ids).prefetch_related("product_type_sizes").order_by("id")
        out = ProductTypeBulkCreateResponseSerializer(qs, many=True).data

        return Response(out, status=status.HTTP_201_CREATED)


class ProductTypeSuggestSortingByModelView(APIView):
    """
    ProductType uchun sorting tavsiya (har bir madel kesimida).
    GET /product-type/<int:madel>/sorting
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, branch, branch_category, madel):
        used = (
            ProductType.objects
            .filter(
                is_delete=False,
                branch_id=branch,
                branch_category_id=branch_category,
                madel_id=madel,
                sorting__isnull=False
            )
            .order_by('sorting')
            .values_list('sorting', flat=True)
        )

        suggested = 1
        for s in used:
            try:
                s_int = int(s)
            except (TypeError, ValueError):
                continue

            if s_int < suggested:
                continue
            if s_int == suggested:
                suggested += 1
            else:
                break

        return Response(
            {
                "branch": branch,
                "branch_category": branch_category,
                "madel": madel,
                "suggested_sorting": suggested,
                "message": "Tavsiya etilgan tartib raqam."
            },
            status=status.HTTP_200_OK
        )