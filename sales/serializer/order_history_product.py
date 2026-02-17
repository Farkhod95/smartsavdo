from rest_framework import serializers
from decimal import Decimal
from django.db import transaction

from accounts.models import Sklad
from inventory.models import Product, ProductStock
from inventory.serializer.product import ProductSerializer
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_model import ProductModelListSerializer
from inventory.serializer.product_type import ProductTypeListSerializer
from inventory.serializer.product_type_size import ProductTypeSizeListSerializer
from sales.models import  OrderHistoryProduct
from sales.serializer.order_history import OrderHistoryListSerializer
from sales.serializer.vozvrat_order import VozvratOrderSerializer


class OrderHistoryProductListSerializer(serializers.ModelSerializer):
    order_history_detail = OrderHistoryListSerializer(source='order_history', read_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)
    sklad_detail = ProductSerializer(source='sklad', read_only=True)
    vozvrat_order_detail = VozvratOrderSerializer(source='vozvrat_order', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'order_history_detail', 'vozvrat_order', 'vozvrat_order_detail',
                  'product', 'product_detail', 'branch', 'branch_detail', 'model', 'model_detail', 'type', 'type_detail',
                  'size', 'size_detail', 'count', 'given_count', 'real_price', 'unit_price', 'wholesale_price',
                  'is_delete', 'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka', 'sklad', 'sklad_detail')


class OrderHistoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'vozvrat_order', 'product', 'branch', 'model', 'type', 'size', 'count',
                  'given_count', 'real_price', 'unit_price', 'wholesale_price', 'is_delete', 'cargo_terminal',
                  'price_difference', 'status_order', 'is_karzinka', 'sklad')


class OrderHistoryProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = (
            'id', 'date',
            'order_history', 'vozvrat_order',
            'product', 'sklad',
            'branch', 'model', 'type', 'size',
            'count', 'given_count',
            'real_price', 'unit_price', 'wholesale_price',
            'is_delete', 'cargo_terminal',
            'price_difference', 'status_order', 'is_karzinka'
        )
        read_only_fields = ('branch', 'model', 'type', 'size', 'real_price', 'is_delete')

    def validate(self, attrs):
        product = attrs.get("product")
        sklad = attrs.get("sklad")
        count = attrs.get("count")

        if not product:
            raise serializers.ValidationError({"product": "product majburiy."})
        if not sklad:
            raise serializers.ValidationError({"sklad": "sklad majburiy."})
        if count is None:
            raise serializers.ValidationError({"count": "count majburiy."})

        try:
            count_int = int(count)
        except Exception:
            raise serializers.ValidationError({"count": "count son bo‘lishi kerak."})

        if count_int <= 0:
            raise serializers.ValidationError({"count": "count 0 dan katta bo‘lishi kerak."})

        if getattr(product, "is_delete", False):
            raise serializers.ValidationError({"product": "Bu product o‘chirilgan (is_delete=True)."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        product: Product = validated_data["product"]
        sklad: Sklad = validated_data["sklad"]
        order_count = int(validated_data["count"])

        # 1) Product row lock
        locked_product = (
            Product.objects
            .select_for_update(of=("self",))
            .get(pk=product.pk)
        )

        if locked_product.is_delete:
            raise serializers.ValidationError({"product": "Bu product o‘chirilgan (is_delete=True)."})

        # 2) ProductStock row lock (ENG MUHIM)
        product_stock = (
            ProductStock.objects
            .select_for_update()
            .filter(product_id=locked_product.pk, sklad_id=sklad.pk)
            .first()
        )

        current_stock = int(product_stock.count or 0) if product_stock else 0

        if current_stock < order_count:
            raise serializers.ValidationError({
                "count": f"Qoldiq yetarli emas. Omborda: {current_stock}, so‘raldi: {order_count}."
            })

        # Productdan FKlarni ko‘chiramiz
        validated_data["branch"] = locked_product.branch
        validated_data["model"] = locked_product.model
        validated_data["type"] = locked_product.type
        validated_data["size"] = locked_product.size
        validated_data["real_price"] = locked_product.real_price

        if validated_data.get("given_count") is None:
            validated_data["given_count"] = order_count

        if user and getattr(user, "is_authenticated", False):
            validated_data["created_by"] = user
            validated_data["updated_by"] = user

        instance = super().create(validated_data)

        # 3) ProductStock kamaytiramiz
        #    (ProductStock yo‘q bo‘lsa bu yerga kelmaydi, chunki current_stock=0 bo‘ladi va yuqorida xato qaytadi)
        product_stock.count = current_stock - order_count
        product_stock.save(update_fields=["count", "updated_time"])

        # 4) Agar Product.count ham real ishlatilsa (umumiy qoldiq):
        if locked_product.count is not None:
            locked_product.count = int(locked_product.count or 0) - order_count
            locked_product.save(update_fields=["count", "updated_time"])

        return instance



