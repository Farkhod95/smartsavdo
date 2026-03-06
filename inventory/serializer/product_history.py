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
    class Meta:
        model = ProductHistory
        fields = (
            'id', 'date', 'filial', 'sklad', 'reserve_limit', 'purchase_invoice',
            'branch', 'branch_category', 'model', 'type', 'size', 'count',
            'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note',
            'product',
        )

    def validate(self, attrs):
        filial = attrs.get('filial')
        sklad = attrs.get('sklad')
        invoice = attrs.get('purchase_invoice')
        count = int(attrs.get('count') or 0)

        if count < 0:
            raise serializers.ValidationError({
                'count': "Miqdor manfiy bo‘lishi mumkin emas."
            })

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
                    'sklad': "Sklad yuborilishi kerak yoki purchase_invoice ichida incoming sklad bo‘lishi shart."
                })

        if invoice:
            # incoming sklad filialga tegishli bo'lsin
            if attrs['filial'] and attrs['sklad'] and getattr(attrs['sklad'], 'filial_id', None):
                if attrs['sklad'].filial_id != attrs['filial'].id:
                    raise serializers.ValidationError({
                        'sklad': "Incoming sklad tanlangan filialga tegishli emas."
                    })

            if invoice.type == PurchaseInvoice.TYPE.INTERNAL:
                if not invoice.sklad_outgoing_id:
                    raise serializers.ValidationError({
                        'purchase_invoice': "INTERNAL invoice uchun sklad_outgoing bo‘lishi shart."
                    })

                if not invoice.sklad_id:
                    raise serializers.ValidationError({
                        'purchase_invoice': "INTERNAL invoice uchun sklad bo‘lishi shart."
                    })

                if invoice.sklad_outgoing_id == invoice.sklad_id:
                    raise serializers.ValidationError({
                        'purchase_invoice': "Ichki kirimda chiqayotgan va kirayotgan sklad bir xil bo‘lishi mumkin emas."
                    })

        return attrs

    def _get_or_create_stock_locked(self, product, sklad):
        stock = (
            ProductStock.objects.select_for_update()
            .filter(product=product, sklad=sklad)
            .first()
        )
        if not stock:
            stock = ProductStock.objects.create(product=product, sklad=sklad, count=0)
        return stock

    def _refresh_invoice_totals(self, invoice_id):
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

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('product', None)

        invoice = validated_data.get('purchase_invoice')
        filial = validated_data['filial']
        incoming_sklad = validated_data['sklad']
        count = int(validated_data.get('count') or 0)

        invoice_type = PurchaseInvoice.TYPE.EXTERNAL
        outgoing_sklad = None

        if invoice:
            invoice_type = invoice.type or PurchaseInvoice.TYPE.EXTERNAL
            if invoice_type == PurchaseInvoice.TYPE.INTERNAL:
                outgoing_sklad = invoice.sklad_outgoing

        # 1) Product ni topamiz
        product = (
            Product.objects.select_for_update()
            .filter(
                filial=filial,
                branch=validated_data['branch'],
                branch_category=validated_data.get('branch_category'),
                model=validated_data.get('model'),
                type=validated_data.get('type'),
                size=validated_data.get('size'),
                is_delete=False,
            )
            .first()
        )

        # 2) Invoice turiga qarab logika
        if invoice_type == PurchaseInvoice.TYPE.EXTERNAL:
            # tashqi kirim: product bo'lmasa yaratamiz
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
                    count=0,  # count ni stockdan recalc qilamiz
                    real_price=validated_data.get('real_price', 0),
                    unit_price=validated_data.get('unit_price', 0),
                    wholesale_price=validated_data.get('wholesale_price', 0),
                    min_price=validated_data.get('min_price', 0),
                    note=validated_data.get('note'),
                    is_delete=False,
                    is_active=True,
                    created_by=validated_data.get('created_by'),
                )
            else:
                # narxlarni yangilab qo'yamiz, countni qo'l bilan oshirmaymiz
                update_data = {
                    'real_price': validated_data.get('real_price', product.real_price),
                    'unit_price': validated_data.get('unit_price', product.unit_price),
                    'wholesale_price': validated_data.get('wholesale_price', product.wholesale_price),
                    'min_price': validated_data.get('min_price', product.min_price),
                    'note': validated_data.get('note', product.note),
                    'reserve_limit': validated_data.get('reserve_limit', product.reserve_limit),
                }
                Product.objects.filter(pk=product.pk).update(**update_data)
                product.refresh_from_db()

            # history yaratamiz
            history = ProductHistory.objects.create(
                product=product,
                **validated_data
            )

            # incoming skladga qo'shamiz
            stock_in = self._get_or_create_stock_locked(product, incoming_sklad)
            ProductStock.objects.filter(pk=stock_in.pk).update(count=F('count') + count)

            # product count stocklardan qayta hisoblanadi
            product.refresh_from_db()
            product.recalc_count_from_stocks(save=True)

        else:
            # INTERNAL
            if not outgoing_sklad:
                raise serializers.ValidationError({
                    'purchase_invoice': "INTERNAL invoice uchun sklad_outgoing topilmadi."
                })

            if outgoing_sklad.id == incoming_sklad.id:
                raise serializers.ValidationError({
                    'purchase_invoice': "Ichki kirimda chiqayotgan va kirayotgan sklad bir xil bo‘lishi mumkin emas."
                })

            if not product:
                raise serializers.ValidationError({
                    'product': "Ichki ko‘chirish uchun avval mahsulot tizimda mavjud bo‘lishi kerak."
                })

            stock_out = self._get_or_create_stock_locked(product, outgoing_sklad)
            stock_in = self._get_or_create_stock_locked(product, incoming_sklad)

            current_out_count = int(stock_out.count or 0)
            if current_out_count < count:
                raise serializers.ValidationError({
                    'count': f"Chiquvchi omborda yetarli mahsulot yo‘q. Mavjud: {current_out_count}, kerak: {count}."
                })

            # history yaratamiz
            history = ProductHistory.objects.create(
                product=product,
                **validated_data
            )

            # source dan ayiramiz
            ProductStock.objects.filter(pk=stock_out.pk).update(count=F('count') - count)

            # destination ga qo'shamiz
            ProductStock.objects.filter(pk=stock_in.pk).update(count=F('count') + count)

            # product umumiy count o'zgarmaydi, lekin baribir recalc qilamiz
            product.refresh_from_db()
            product.recalc_count_from_stocks(save=True)

        # 3) invoice aggregation
        if history.purchase_invoice_id:
            self._refresh_invoice_totals(history.purchase_invoice_id)

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