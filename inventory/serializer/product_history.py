from rest_framework import serializers
from django.db import transaction

from inventory.models import Product, ProductHistory
from inventory.serializer.product import ProductListSerializer
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_branch_category import ProductBranchCategorySerializer
from inventory.serializer.product_model import ProductModelListSerializer
from inventory.serializer.product_type import ProductTypeListSerializer
from inventory.serializer.product_type_size import ProductTypeSizeListSerializer
from suppliers.serializers import PurchaseInvoiceSerializer


class ProductHistoryListSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)
    purchase_invoice_detail = PurchaseInvoiceSerializer(source='purchase_invoice', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'filial', 'product_detail', 'purchase_invoice', 'purchase_invoice_detail', 'branch', 'branch_detail', 'branch_category', 'branch_category_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')


class ProductHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHistory
        fields = ('id', 'date', 'reserve_limit', 'product', 'filial', 'purchase_invoice', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')




class ProductHistoryCreateSerializer(serializers.ModelSerializer):
    """
    ProductHistory yaratadi, lekin product maydoni o‘rniga product_data qabul qiladi.
    """
    # product_data = ProductCreateSerializer(write_only=True)

    class Meta:
        model = ProductHistory
        fields = (
            'id', 'date', 'filial', 'reserve_limit', 'purchase_invoice', 'branch', 'branch_category', 'model', 'type', 'size', 'count', 'real_price',
            'unit_price', 'wholesale_price', 'min_price', 'note',
            'product',       # response’da ko‘rinsin
            # 'product_data',  # request’da keladi
        )
        read_only_fields = ('id', 'product')

    def validate(self, attrs):
        """
        filial payload’da kelmasa, purchase_invoice.filial dan olib qo'yamiz.
        Ikkalasi ham bo'lmasa xato.
        """
        filial = attrs.get('filial')
        invoice = attrs.get('purchase_invoice')

        if not filial:
            if invoice and getattr(invoice, 'filial_id', None):
                attrs['filial'] = invoice.filial
            else:
                raise serializers.ValidationError({
                    'filial': "Filial yuborilishi kerak yoki purchase_invoice ichida filial bo‘lishi shart."
                })
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # filial endi aniq bor (validate ichida qo‘yilgan bo‘ladi)
        filial = validated_data['filial']

        # 1) Product yaratamiz (payload fieldlari asosida)
        product = Product.objects.create(
            date=validated_data.get('date'),
            reserve_limit=validated_data.get('reserve_limit'),
            filial=filial,
            branch=validated_data.get('branch'),
            branch_category=validated_data.get('branch_category'),
            model=validated_data.get('model'),
            type=validated_data.get('type'),
            size=validated_data.get('size'),
            count=validated_data.get('count'),
            real_price=validated_data.get('real_price', 0),
            unit_price=validated_data.get('unit_price', 0),
            wholesale_price=validated_data.get('wholesale_price', 0),
            min_price=validated_data.get('min_price', 0),
            note=validated_data.get('note'),
            is_delete=False,
        )

        # 2) ProductHistory yaratamiz va product ni bog'laymiz
        history = ProductHistory.objects.create(
            product=product,
            **validated_data
        )
        return history