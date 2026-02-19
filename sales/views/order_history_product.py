from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.db import transaction
from django.db.models import F

from inventory.models import Product, ProductStock
from sales.filterset import OrderHistoryProductFilter
from sales.models import OrderHistoryProduct

from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from sales.serializer.order_history_product import OrderHistoryProductSerializer, OrderHistoryProductListSerializer, \
    OrderHistoryProductCreateSerializer, OrderHistoryProductVozvratCreateSerializer, OrderHistoryProductUpdateSerializer


class OrderHistoryProductFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
        field_info = []
        for field in OrderHistoryProduct._meta.fields:
            field_info.append({
                "field_name": field.name,
                "verbose_name": str(field.verbose_name),
                "help_text": str(field.help_text) if field.help_text else "",
                "type": field.get_internal_type(),
                "max_length": getattr(field, 'max_length', None),
                "choices": dict(field.choices) if field.choices else None
            })
        return Response(field_info)


class OrderHistoryProductViewList(ListCreateAPIView):
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
    permission_classes = (AllowAny,)
    authentication_classes = []
    serializer_class = OrderHistoryProductSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryProductFilter
    search_fields = ('order_history__id', 'vozvrat_order__id', 'cargo_terminal', 'model__name', 'type__name')
    ordering = ['pk']
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        return OrderHistoryProduct.objects.filter(is_delete=False)


class OrderHistoryProductView(ListCreateAPIView):
    serializer_class = OrderHistoryProductListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryProductFilter
    search_fields = ('order_history__id', 'vozvrat_order__id', 'cargo_terminal', 'model__name', 'type__name')
    ordering = ['pk']

    def get_queryset(self):
        return OrderHistoryProduct.objects.filter(is_delete=False)

    def post(self, request):
        serializer = OrderHistoryProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class OrderHistoryProductDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderHistoryProductSerializer

    def get_queryset(self):
        return OrderHistoryProduct.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get(self, request, pk):
        instance = get_object_or_404(OrderHistoryProduct, id=pk)
        serializer = OrderHistoryProductListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = get_object_or_404(OrderHistoryProduct, id=pk, is_delete=False)
        serializer = OrderHistoryProductUpdateSerializer(
            instance,
            data=request.data,
            partial=False,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        """
        Soft delete + stock rollback.
        Sale bo'lsa: +count qaytaradi
        Vozvrat bo'lsa: -count qaytaradi (vozvratni bekor qiladi)
        """
        item = get_object_or_404(
            OrderHistoryProduct.objects.select_for_update(),
            id=pk,
            is_delete=False
        )

        product_id = item.product_id
        sklad_id = item.sklad_id
        cnt = int(item.count or 0)

        # vozvratmi?
        is_vozvrat = bool(item.vozvrat_order_id)
        sign = 1 if is_vozvrat else -1

        # rollback delta = -sign * cnt
        delta = -sign * cnt

        # lock rows
        prod = Product.objects.select_for_update(of=("self",)).get(pk=product_id)
        stock, _ = ProductStock.objects.select_for_update().get_or_create(
            product_id=product_id,
            sklad_id=sklad_id,
            defaults={"count": 0}
        )

        # apply delta (manfiy bo‘lib qolmasin)
        current_stock = int(stock.count or 0)
        new_stock = current_stock + delta
        if new_stock < 0:
            raise serializers.ValidationError({
                "detail": f"Ombor qoldig‘i manfiy bo‘lib qolyapti. Hozir: {current_stock}, rollback: {delta}."
            })

        stock.count = new_stock
        stock.save(update_fields=["count", "updated_time"])

        if prod.count is not None:
            pcur = int(prod.count or 0)
            pnew = pcur + delta
            if pnew < 0:
                raise serializers.ValidationError({
                    "detail": f"Product.count manfiy bo‘lib qolyapti. Hozir: {pcur}, rollback: {delta}."
                })
            prod.count = pnew
            prod.save(update_fields=["count", "updated_time"])

        # soft delete
        item.is_delete = True
        item.save(update_fields=["is_delete", "updated_time"])

        return Response(nonContent(), status=status.HTTP_204_NO_CONTENT)


class OrderHistoryProductVozvratView(ListCreateAPIView):
    serializer_class = OrderHistoryProductListSerializer
    pagination_class = ResultsSetPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend)
    filterset_class = OrderHistoryProductFilter
    search_fields = ('order_history__id', 'vozvrat_order__id', 'cargo_terminal', 'model__name', 'type__name')
    ordering = ['pk']

    def get_queryset(self):
        return OrderHistoryProduct.objects.filter(is_delete=False)

    def post(self, request):
        serializer = OrderHistoryProductVozvratCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)