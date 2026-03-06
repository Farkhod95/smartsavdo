from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import F
from django.db.models import Count

from rest_framework import filters, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from inventory.filterset import ProductHistoryFilter
from inventory.models import ProductHistory, Product, ProductStock
from inventory.serializer.product_history import ProductHistoryListSerializer, ProductHistorySerializer, \
    ProductHistoryCreateSerializer, ProductHistoryPutSerializer
from restapp.pagination import ResultsSetPagination
from restapp.utils.responses import nonContent
from suppliers.models import PurchaseInvoice


class ProductHistoryFieldInfoView(APIView):
    permission_classes = [IsAuthenticated, ]

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
    """
    Public list (faqat GET), DistrictViewList kabi.
    """
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
    #
    # def perform_create(self, serializer):
    #     # BaseModel’da created_by bo‘lsa shu yerda berib yuboramiz
    #     serializer.save(created_by=self.request.user)
    def post(self, request):
        serializer = ProductHistoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status.HTTP_201_CREATED)


def resolve_sklad(history: ProductHistory, payload_sklad=None, payload_invoice=None):
    """
    Skladni topish tartibi:
    1) payload_sklad bo'lsa
    2) history.sklad bo'lsa
    3) payload_invoice.sklad bo'lsa
    4) history.purchase_invoice.sklad bo'lsa
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


class ProductHistoryDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductHistorySerializer

    def get_queryset(self):
        return ProductHistory.objects.select_related('product', 'sklad', 'purchase_invoice').all()

    def get(self, request, pk):
        instance = get_object_or_404(self.get_queryset(), id=pk)
        serializer = ProductHistoryListSerializer(instance, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def put(self, request, pk):
        history = get_object_or_404(self.get_queryset().select_for_update(), id=pk)

        # Siz aytgandek: product doim aniq va o'zgarmaydi
        if not history.product_id:
            raise ValidationError({"product": "ProductHistory.product topilmadi."})

        product = Product.objects.select_for_update().get(pk=history.product_id)

        # OLD invoice
        old_invoice = history.purchase_invoice

        # payload validate
        put_ser = ProductHistoryPutSerializer(history, data=request.data, context={'request': request})
        put_ser.is_valid(raise_exception=True)
        data = put_ser.validated_data

        # NEW invoice
        new_invoice = data.get('purchase_invoice', history.purchase_invoice)

        # OLD
        old_count = history.count or 0

        old_sklad = resolve_sklad(history)
        if old_sklad is None:
            raise ValidationError({"sklad": "Eski sklad topilmadi (historyda ham, invoice ichida ham yo‘q)."})

        # NEW (sklad payload’da bo‘lmasa invoice.sklad dan)
        new_invoice = data.get('purchase_invoice', history.purchase_invoice)
        new_sklad = resolve_sklad(history, payload_sklad=data.get('sklad'), payload_invoice=new_invoice)
        if new_sklad is None:
            raise ValidationError({"sklad": "Yangi sklad topilmadi (payload/history/invoice)."})

        new_count = data.get('count', history.count)
        if new_count is None:
            new_count = history.count or 0

        # signed delta (minus ham bo'lishi mumkin)
        delta = new_count - old_count

        # --- 1) Product.count update (delta) ---
        # manfiyga tushishi mumkin => hech qanday <0 tekshiruv yo'q
        if delta != 0:
            Product.objects.filter(pk=product.pk).update(count=F('count') + delta)

        # --- 2) Stock update ---
        same_sklad = (old_sklad.id == new_sklad.id)

        if same_sklad:
            # bitta sklad: stockga faqat delta
            if delta != 0:
                stock = (
                    ProductStock.objects.select_for_update()
                    .filter(product=product, sklad=old_sklad)
                    .first()
                )
                if not stock:
                    # old_count=0 bo'lsa stock bo'lmasligi mumkin
                    stock = ProductStock.objects.create(product=product, sklad=old_sklad, count=0)

                ProductStock.objects.filter(pk=stock.pk).update(count=F('count') + delta)

        else:
            # sklad ALMASHDI:
            # 1) eski sklad ta'sirini bekor qilish: old_stock.count -= old_count
            if old_count != 0:
                old_stock = (
                    ProductStock.objects.select_for_update()
                    .filter(product=product, sklad=old_sklad)
                    .first()
                )
                if not old_stock:
                    # old_count 0 bo'lmaganda odatda bo'lishi kerak,
                    # lekin bo'lmasa ham yaratib, keyin -old_count qilamiz (bizda manfiyga ruxsat bor)
                    old_stock = ProductStock.objects.create(product=product, sklad=old_sklad, count=0)

                ProductStock.objects.filter(pk=old_stock.pk).update(count=F('count') - old_count)

            # 2) yangi skladga yangi ta'sir: new_stock.count += new_count
            if new_count != 0:
                new_stock = (
                    ProductStock.objects.select_for_update()
                    .filter(product=product, sklad=new_sklad)
                    .first()
                )
                if not new_stock:
                    new_stock = ProductStock.objects.create(product=product, sklad=new_sklad, count=0)

                ProductStock.objects.filter(pk=new_stock.pk).update(count=F('count') + new_count)

        # --- 3) History update (product o'zgarmaydi) ---
        for field, value in data.items():
            setattr(history, field, value)

        # resolved skladni doim yozib qo'yamiz
        history.sklad = new_sklad
        history.count = new_count
        history.updated_by = request.user
        history.save()

        # =========================
        # PurchaseInvoice.product_count update
        # faqat invoice_id bo'lsa
        # =========================
        invoice_ids = set()

        if old_invoice and old_invoice.id:
            invoice_ids.add(old_invoice.id)

        if history.purchase_invoice and history.purchase_invoice.id:
            invoice_ids.add(history.purchase_invoice.id)

        for invoice_id in invoice_ids:
            product_count = ProductHistory.objects.filter(
                purchase_invoice_id=invoice_id
            ).count()

            PurchaseInvoice.objects.filter(id=invoice_id).update(
                product_count=product_count
            )

        out = ProductHistoryListSerializer(history, context={'request': request})
        return Response(out.data, status=status.HTTP_202_ACCEPTED)

    @transaction.atomic
    def delete(self, request, pk):
        history = get_object_or_404(self.get_queryset().select_for_update(), id=pk)

        if not history.product_id:
            raise ValidationError({"product": "ProductHistory.product topilmadi."})

        product = Product.objects.select_for_update().get(pk=history.product_id)

        sklad = resolve_sklad(history)
        if sklad is None:
            raise ValidationError({"sklad": "Sklad topilmadi (historyda ham, invoice ichida ham yo‘q)."})

        count = history.count or 0

        # count 0 bo'lsa: product/stock o'zgarmaydi
        if count != 0:
            stock = (
                ProductStock.objects.select_for_update()
                .filter(product=product, sklad=sklad)
                .first()
            )
            if not stock:
                # stock bo'lmasa ham yaratib, keyin -count qilamiz (manfiyga ruxsat bor)
                stock = ProductStock.objects.create(product=product, sklad=sklad, count=0)

            # history ta'sirini bekor qilamiz:
            # product.count -= count
            # stock.count   -= count
            Product.objects.filter(pk=product.pk).update(count=F('count') - count)
            ProductStock.objects.filter(pk=stock.pk).update(count=F('count') - count)

        history.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



# class ProductHistoryDetailView(RetrieveUpdateDestroyAPIView):
#     serializer_class = ProductHistorySerializer
#
#     def get_queryset(self):
#         return ProductHistory.objects.all()
#
#     def perform_update(self, serializer):
#         serializer.save(updated_by=self.request.user)
#
#     def get(self, request, pk):
#         instance = get_object_or_404(ProductHistory, id=pk)
#         serializer = ProductHistoryListSerializer(instance)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     def put(self, request, pk):
#         instance = get_object_or_404(ProductHistory, id=pk)
#         serializer = self.serializer_class(instance, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(updated_by=self.request.user)
#         return Response(serializer.data, status.HTTP_202_ACCEPTED)
#
#     def delete(self, request, pk):
#         instance = get_object_or_404(ProductHistory, id=pk)
#         instance.delete()
#         return Response(nonContent(), status.HTTP_204_NO_CONTENT)
