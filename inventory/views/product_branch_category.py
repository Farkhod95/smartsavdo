from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from restapp.pagination import ResultsSetPagination
from inventory.filterset import ProductBranchCategoryFilter
from inventory.models import ProductBranchCategory
from inventory.serializer.product_branch_category import ProductBranchCategorySerializer, ProductBranchCategoryListSerializer


class ProductBranchCategoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_info = []
        for field in ProductBranchCategory._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ProductBranchCategoryView(ListCreateAPIView):
    serializer_class = ProductBranchCategoryListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductBranchCategoryFilter
    search_fields = ('name',)
    ordering = ['sorting', '-id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductBranchCategory.objects.select_related('product_branch').all()

    def post(self, request, **kwargs):
        serializer = ProductBranchCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ProductBranchCategoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductBranchCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductBranchCategory.objects.select_related('product_branch').all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        obj = get_object_or_404(ProductBranchCategory, id=pk)
        serializer = ProductBranchCategoryListSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = get_object_or_404(ProductBranchCategory, id=pk)
        serializer = self.serializer_class(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)



class ProductBranchCategorySuggestSortingByBranchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_branch):
        used = (
            ProductBranchCategory.objects
            .filter(
                is_delete=False,
                product_branch_id=product_branch,
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
                "product_branch": product_branch,
                "suggested_sorting": suggested,
                "message": "Tavsiya etilgan tartib raqam."
            },
            status=status.HTTP_200_OK
        )