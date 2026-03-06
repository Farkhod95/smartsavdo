from rest_framework import serializers
from django.db import transaction
from django.db.models import F, Sum, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce

from accounts.serializers import FilialSerializer, SkladSerializer
from inventory.models import Product, ProductHistory, ProductStock
from inventory.serializer.product import ProductSerializer
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_branch_category import ProductBranchCategorySerializer
from inventory.serializer.product_model import ProductModelSerializer
from inventory.serializer.product_type import ProductTypeSerializer
from inventory.serializer.product_type_size import ProductTypeSizeSerializer
from suppliers.models import PurchaseInvoice
from suppliers.serializer.purchase_invoice import PurchaseInvoiceSerializer


class ProductHistoryListSerializer(serializers.ModelSerializer):
    filial_detail = FilialSerializer(source='filial', read_only=True)
    sklad_detail = SkladSerializer(source='sklad', read_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)
    purchase_invoice_detail = PurchaseInvoiceSerializer(source='purchase_invoice', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)
    model_detail = ProductModelSerializer(source='model', read_only=True)
    type_detail = ProductTypeSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeSerializer(source='size', read_only=True)

    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'filial', 'filial_detail', 'sklad', 'sklad_detail', 'product_detail', 'purchase_invoice', 'purchase_invoice_detail', 'branch', 'branch_detail', 'branch_category', 'branch_category_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')


class ProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'filial', 'sklad', 'purchase_invoice', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')




class ProductHistoryCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratadi, lekin product maydoni o‘rniga product_data qabul qiladi.
    """
    # product_data = ProductCreateSerializer(write_only=True)

    class Meta:
        model = ProductHistory
        fields = (
            'id', 'date', 'filial', 'sklad', 'reserve_limit', 'purchase_invoice', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price',
            'unit_price', 'wholesale_price', 'min_price', 'note',
            'product',       # response’da ko‘rinsin
            # 'product_data',  # request’da keladi
        )
        # read_only_fields = ('id', 'product')

    def validate(self, attrs):
        """
        filial payload’da kelmasa, purchase_invoice.filial dan olib qo'yamiz.
        Ikkalasi ham bo'lmasa xato.
        """
        filial = attrs.get('filial')
        sklad = attrs.get('sklad')
        invoice = attrs.get('purchase_invoice')

        if not filial:
            if invoice and getattr(invoice, 'filial_id', None):
                attrs['filial'] = invoice.filial
            else:
                raise serializers.ValidationError({
                    'filial': "Filial yuborilishi kerak yoki purchase_invoice ichida filial bo‘lishi shart."
                })

        if not sklad:
            if invoice and getattr(invoice, 'sklad_id', None):
                attrs['sklad'] = invoice.sklad
            else:
                raise serializers.ValidationError({
                    'sklad': "Sklad yuborilishi kerak yoki purchase_invoice ichida sklad bo‘lishi shart."
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # safety: product field bo'lsa ham olib tashlaymiz
        validated_data.pop('product', None)

        # filial endi aniq bor (validate ichida qo‘yilgan bo‘ladi)
        filial = validated_data['filial']
        count = validated_data.get('count') or 0

        # 1) Product yaratamiz (payload fieldlari asosida)
        product_qs = Product.objects.select_for_update().filter(
            filial=filial,
            branch=validated_data['branch'],
            branch_category=validated_data.get('branch_category'),
            model=validated_data.get('model'),
            type=validated_data.get('type'),
            size=validated_data.get('size'),
            is_delete=False,
        )

        product = product_qs.first()

        if not product:
            product = Product.objects.create(
                date=validated_data.get('date'),
                reserve_limit=validated_data.get('reserve_limit'),
                filial=filial,
                branch=validated_data.get('branch'),
                branch_category=validated_data.get('branch_category'),
                model=validated_data.get('model'),
                type=validated_data.get('type'),
                size=validated_data.get('size'),
                count=count,
                real_price=validated_data.get('real_price', 0),
                unit_price=validated_data.get('unit_price', 0),
                wholesale_price=validated_data.get('wholesale_price', 0),
                min_price=validated_data.get('min_price', 0),
                note=validated_data.get('note'),
                is_delete=False,
            )
        else:
            # count ni xavfsiz oshiramiz
            Product.objects.filter(pk=product.pk).update(
                count=F('count') + count,
                real_price=validated_data.get('real_price', product.real_price),
                unit_price=validated_data.get('unit_price', product.unit_price),
                wholesale_price=validated_data.get('wholesale_price', product.wholesale_price),
                min_price=validated_data.get('min_price', product.min_price),
                note=validated_data.get('note', product.note),
                reserve_limit=validated_data.get('reserve_limit', product.reserve_limit),
            )
            product.refresh_from_db()

        # 2) ProductHistory yaratamiz va product ni bog'laymiz
        history = ProductHistory.objects.create(
            product=product,
            **validated_data
        )

        # 3) ProductStock update
        sklad = history.sklad
        product_stock = ProductStock.objects.select_for_update().filter(
            product=product,
            sklad=sklad
        ).first()

        if not product_stock:
            ProductStock.objects.create(product=product, sklad=sklad, count=count)
        else:
            ProductStock.objects.filter(pk=product_stock.pk).update(count=F('count') + count)

        # 4) PurchaseInvoice.product_count + all_product_summa update
        if history.purchase_invoice_id:
            aggregates = ProductHistory.objects.filter(
                purchase_invoice_id=history.purchase_invoice_id
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

            PurchaseInvoice.objects.filter(id=history.purchase_invoice_id).update(
                product_count=aggregates['product_count'] or 0,
                all_product_summa=aggregates['all_product_summa'] or 0
            )

        return history


class ProductHistoryPutSerializer(serializers.ModelSerializer):
    """
    count: musbat, manfiy, 0 => hammasi mumkin.
    """
    class Meta:
        model = ProductHistory
        fields = (
            'date', 'reserve_limit', 'sklad', 'purchase_invoice',
            'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note'
        )

    def validate(self, attrs):
        # count null bo'lmasin (0 mumkin)
        if 'count' in attrs and attrs['count'] is None:
            raise serializers.ValidationError({'count': "Count null bo‘lishi mumkin emas."})
        return attrs