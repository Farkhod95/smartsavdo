from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.filterset import ProductTypeSizeFilter
from inventory.models import ProductTypeSize
from inventory.serializers import ProductTypeSizeListSerializer, ProductTypeSizeSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent


class ProductTypeSizeFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in ProductTypeSize._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class ProductTypeSizeViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = ProductTypeSizeSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductTypeSizeFilter
    search_fields = ('product_type__name', 'type__code', 'type__name')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return ProductTypeSize.objects.filter(is_delete=False)


class ProductTypeSizeView(ListCreateAPIView):
    serializer_class = ProductTypeSizeListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = ProductTypeSizeFilter
    search_fields = ('product_type__name', 'type__code', 'type__name')
    ordering = ['pk']

    def get_queryset(self):
        return ProductTypeSize.objects.filter(is_delete=False)

    def post(self, request):
        serializer = ProductTypeSizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class ProductTypeSizeDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductTypeSizeSerializer

    def get_queryset(self):
        return ProductTypeSize.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(ProductTypeSize, id=pk)
        serializer = ProductTypeSizeListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(ProductTypeSize, id=pk)
        serializer = self.serializer_class(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=self.request.user)
        return Response(serializer.data, status.HTTP_202_ACCEPTED)

    def delete(self, request, pk):
        instance = get_object_or_404(ProductTypeSize, id=pk)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])
        return Response(nonContent(), status.HTTP_204_NO_CONTENT)
