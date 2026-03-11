from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce

from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from inventory.filterset import ProductHistoryFilter
from inventory.models import ProductHistory, Product, ProductStock
from inventory.serializer.product_history import (
    ProductHistoryListSerializer,
    ProductHistorySerializer,
    ProductHistoryCreateSerializer,
    ProductHistoryPutSerializer,
)
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.models import PurchaseInvoice


class ProductHistoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated]

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
    search_fields = ('note', 'product__id', 'purchase_invoice__id', 'filial__name', 'sklad__name', 'branch__name', 'model__name', 'type__name')
    ordering = ['-pk']

    def get_queryset(self):
        return ProductHistory.objects.all()

    def post(self, request):
        serializer = ProductHistoryCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def resolve_sklad(history: ProductHistory, payload_sklad=None, payload_invoice=None):
    """
    Incoming skladni topish:
    1) payload_sklad
    2) history.sklad
    3) payload_invoice.sklad
    4) history.purchase_invoice.sklad
    """
    if payload_sklad is not None:
        return payload_sklad
    if getattr(history, 'sklad_id', None):
        return history.sklad
    if payload_invoice and getattr(payload_invoice, 'sklad_id', None):
        return payload_invoice.sklad
    inv = getattr(history, 'purchase_invoice', None)
    if inv and getattr(inv, 'sklad_id', None):
        return inv.sklad
    return None


def resolve_outgoing_sklad(history: ProductHistory, payload_invoice=None):
    """
    INTERNAL bo'lsa source skladni topish:
    1) payload_invoice.sklad_outgoing
    2) history.purchase_invoice.sklad_outgoing
    """
    if payload_invoice and getattr(payload_invoice, 'sklad_outgoing_id', None):
        return payload_invoice.sklad_outgoing
    inv = getattr(history, 'purchase_invoice', None)
    if inv and getattr(inv, 'sklad_outgoing_id', None):
        return inv.sklad_outgoing
    return None


def resolve_invoice_type(history: ProductHistory, payload_invoice=None):
    if payload_invoice and getattr(payload_invoice, 'type', None):
        return payload_invoice.type
    inv = getattr(history, 'purchase_invoice', None)
    if inv and getattr(inv, 'type', None):
        return inv.type
    return PurchaseInvoice.TYPE.EXTERNAL


def get_or_create_stock_locked(product, sklad):
    stock = (
        ProductStock.objects.select_for_update()
        .filter(product=product, sklad=sklad)
        .first()
    )
    if not stock:
        stock = ProductStock.objects.create(product=product, sklad=sklad, count=0)
    return stock


def apply_history_stock_effect(*, product, invoice_type, incoming_sklad, outgoing_sklad, qty, reverse=False):
    """
    reverse=False => history ta'sirini qo'llash
    reverse=True  => history ta'sirini BEKOR qilish

    EXTERNAL:
        apply   => incoming +qty
        reverse => incoming -qty

    INTERNAL:
        apply   => outgoing -qty, incoming +qty
        reverse => outgoing +qty, incoming -qty
    """
    qty = int(qty or 0)
    if qty == 0:
        return

    if not incoming_sklad:
        raise ValidationError({"sklad": "Incoming sklad topilmadi."})

    if invoice_type == PurchaseInvoice.TYPE.INTERNAL:
        if not outgoing_sklad:
            raise ValidationError({"sklad_outgoing": "INTERNAL uchun outgoing sklad topilmadi."})
        if outgoing_sklad.id == incoming_sklad.id:
            raise ValidationError({"sklad": "Ichki kirimda chiqayotgan va kirayotgan sklad bir xil bo‘lishi mumkin emas."})

    if invoice_type == PurchaseInvoice.TYPE.EXTERNAL:
        stock_in = get_or_create_stock_locked(product, incoming_sklad)
        if reverse:
            ProductStock.objects.filter(pk=stock_in.pk).update(count=F('count') - qty)
        else:
            ProductStock.objects.filter(pk=stock_in.pk).update(count=F('count') + qty)
        return

    # INTERNAL
    stock_out = get_or_create_stock_locked(product, outgoing_sklad)
    stock_in = get_or_create_stock_locked(product, incoming_sklad)

    if reverse:
        ProductStock.objects.filter(pk=stock_out.pk).update(count=F('count') + qty)
        ProductStock.objects.filter(pk=stock_in.pk).update(count=F('count') - qty)
    else:
        ProductStock.objects.filter(pk=stock_out.pk).update(count=F('count') - qty)
        ProductStock.objects.filter(pk=stock_in.pk).update(count=F('count') + qty)


def refresh_invoice_totals(invoice_id):
    if not invoice_id:
        return

    aggregates = ProductHistory.objects.filter(
        purchase_invoice_id=invoice_id
    ).aggregate(
        product_count=Coalesce(Sum('count'), 0),
        all_product_summa=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('count') * F('real_price'),
                    output_field=DecimalField(max_digits=20, decimal_places=2)
                )
            ),
            0,
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )
    )

    PurchaseInvoice.objects.filter(id=invoice_id).update(
        product_count=aggregates['product_count'] or 0,
        all_product_summa=aggregates['all_product_summa'] or 0
    )


class ProductHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductHistorySerializer

    def get_queryset(self):
        return ProductHistory.objects.select_related(
            'product',
            'sklad',
            'purchase_invoice',
            'purchase_invoice__sklad',
            'purchase_invoice__sklad_outgoing',
        ).all()

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = ProductHistoryListSerializer(instance, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def patch(self, request, pk):
        return self._update_history(request, pk, partial=True)

    @transaction.atomic
    def put(self, request, pk):
        return self._update_history(request, pk, partial=False)

    def _update_history(self, request, pk, partial=False):
        history = get_object_or_404(
            ProductHistory.objects.select_for_update(),
            id=pk
        )

        if not history.product_id:
            raise ValidationError({"product": "ProductHistory.product topilmadi."})

        product = Product.objects.select_for_update().get(pk=history.product_id)

        old_invoice = history.purchase_invoice
        old_invoice_id = old_invoice.id if old_invoice else None
        old_invoice_type = resolve_invoice_type(history)
        old_incoming_sklad = resolve_sklad(history)
        old_outgoing_sklad = resolve_outgoing_sklad(history)
        old_count = int(history.count or 0)

        if old_incoming_sklad is None:
            raise ValidationError({"sklad": "Eski incoming sklad topilmadi."})

        serializer = ProductHistoryPutSerializer(
            history,
            data=request.data,
            partial=partial,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        new_invoice = data.get('purchase_invoice', history.purchase_invoice)
        new_invoice_id = new_invoice.id if new_invoice else None
        new_invoice_type = resolve_invoice_type(history, payload_invoice=new_invoice)
        new_incoming_sklad = resolve_sklad(
            history,
            payload_sklad=data.get('sklad'),
            payload_invoice=new_invoice
        )
        new_outgoing_sklad = resolve_outgoing_sklad(history, payload_invoice=new_invoice)
        new_count = int(data.get('count', history.count or 0) or 0)

        if new_incoming_sklad is None:
            raise ValidationError({"sklad": "Yangi incoming sklad topilmadi."})

        # 1) eski ta'sirni bekor qilamiz
        apply_history_stock_effect(
            product=product,
            invoice_type=old_invoice_type,
            incoming_sklad=old_incoming_sklad,
            outgoing_sklad=old_outgoing_sklad,
            qty=old_count,
            reverse=True
        )

        # 2) history fieldlarni yangilaymiz
        for field, value in data.items():
            setattr(history, field, value)

        history.sklad = new_incoming_sklad
        history.count = new_count
        history.updated_by = request.user
        history.save()

        # 3) yangi ta'sirni qo'llaymiz
        apply_history_stock_effect(
            product=product,
            invoice_type=new_invoice_type,
            incoming_sklad=new_incoming_sklad,
            outgoing_sklad=new_outgoing_sklad,
            qty=new_count,
            reverse=False
        )

        # 4) product umumiy count qayta hisoblanadi
        product.refresh_from_db()
        product.recalc_count_from_stocks(save=True)

        # 5) invoice aggregation
        invoice_ids = set()
        if old_invoice_id:
            invoice_ids.add(old_invoice_id)
        if new_invoice_id:
            invoice_ids.add(new_invoice_id)

        for invoice_id in invoice_ids:
            refresh_invoice_totals(invoice_id)

        out = ProductHistoryListSerializer(history, context={'request': request})
        return Response(out.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        history = get_object_or_404(
            ProductHistory.objects.select_for_update(),
            id=pk
        )

        if not history.product_id:
            raise ValidationError({"product": "ProductHistory.product topilmadi."})

        product = Product.objects.select_for_update().get(pk=history.product_id)

        old_invoice_id = history.purchase_invoice_id
        invoice_type = resolve_invoice_type(history)
        incoming_sklad = resolve_sklad(history)
        outgoing_sklad = resolve_outgoing_sklad(history)
        count = int(history.count or 0)

        if incoming_sklad is None:
            raise ValidationError({"sklad": "Incoming sklad topilmadi."})

        # history ta'sirini bekor qilamiz
        apply_history_stock_effect(
            product=product,
            invoice_type=invoice_type,
            incoming_sklad=incoming_sklad,
            outgoing_sklad=outgoing_sklad,
            qty=count,
            reverse=True
        )

        history.delete()

        product.refresh_from_db()
        product.recalc_count_from_stocks(save=True)

        if old_invoice_id:
            refresh_invoice_totals(old_invoice_id)

        return Response(status=status.HTTP_204_NO_CONTENT)