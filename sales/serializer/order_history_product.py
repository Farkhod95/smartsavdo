from rest_framework import serializers
from decimal import Decimal
from django.db import transaction

from accounts.models import Sklad
from accounts.serializers import SkladForSerializer
from inventory.models import Product, ProductStock
from inventory.serializer.product import ProductForSerializer
from inventory.serializer.product_branch import ProductBranchForSerializer
from inventory.serializer.product_branch_category import ProductBranchCategoryForSerializer
from inventory.serializer.product_model import ProductModelForSerializer
from inventory.serializer.product_type import ProductTypeForSerializer
from inventory.serializer.product_type_size import  ProductTypeSizeForSerializer
from sales.models import  OrderHistoryProduct
from sales.serializer.order_history import  OrderHistoryForSerializer
from sales.serializer.vozvrat_order import VozvratOrderSerializer


class OrderHistoryProductListSerializer(serializers.ModelSerializer):
    order_history_detail = OrderHistoryForSerializer(source='order_history', read_only=True)
    product_detail = ProductForSerializer(source='product', read_only=True)
    sklad_detail = SkladForSerializer(source='sklad', read_only=True)
    vozvrat_order_detail = VozvratOrderSerializer(source="vozvrat_order", read_only=True)

    branch_detail = ProductBranchForSerializer(source="branch", read_only=True)
    branch_category_detail = ProductBranchCategoryForSerializer(source="branch_category", read_only=True)

    model_detail = ProductModelForSerializer(source="model", read_only=True)
    type_detail = ProductTypeForSerializer(source="type", read_only=True)
    size_detail = ProductTypeSizeForSerializer(source="size", read_only=True)

    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'order_history_detail', 'vozvrat_order', 'vozvrat_order_detail',
                  'product', 'product_detail', 'branch', 'branch_detail', 'branch_category', 'branch_category_detail',
                  'model', 'model_detail', 'type', 'type_detail',
                  'size', 'size_detail', 'count', 'given_count', 'real_price', 'unit_price', 'wholesale_price',
                  'is_delete', 'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka', 'sklad', 'sklad_detail',
                  'price_dollar', 'price_sum')


class OrderHistoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'vozvrat_order', 'product', 'branch', 'branch_category', 'model', 'type', 'size', 'count',
                  'given_count', 'real_price', 'unit_price', 'wholesale_price', 'is_delete', 'cargo_terminal',
                  'price_difference', 'status_order', 'is_karzinka', 'sklad', 'price_dollar', 'price_sum')


class OrderHistoryProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = (
            'id', 'date',
            'order_history', 'vozvrat_order',
            'product', 'sklad',
            'branch', 'branch_category', 'model', 'type', 'size',
            'count', 'given_count', 'price_dollar', 'price_sum',
            'real_price', 'unit_price', 'wholesale_price',
            'is_delete', 'cargo_terminal',
            'price_difference', 'status_order', 'is_karzinka'
        )
        # read_only_fields = ('branch', 'model', 'type', 'size', 'real_price', 'is_delete')

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
        validated_data["branch_category"] = locked_product.branch_category
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


class OrderHistoryProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = (
            'id', 'date',
            'order_history', 'vozvrat_order',
            'product', 'sklad',
            'count', 'given_count',
            'price_dollar', 'price_sum',
            'real_price', 'unit_price', 'wholesale_price',
            'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka',
            'is_delete',
        )

    # ---- helpers ----

    def _to_int(self, v, field_name="count"):
        try:
            x = int(v)
        except Exception:
            raise serializers.ValidationError({field_name: f"{field_name} son bo‘lishi kerak."})
        if x <= 0:
            raise serializers.ValidationError({field_name: f"{field_name} 0 dan katta bo‘lishi kerak."})
        return x

    def _is_vozvrat(self, instance: OrderHistoryProduct, validated_data) -> bool:
        # updated state bo‘yicha aniqlaymiz
        vozvrat_order = validated_data.get("vozvrat_order", instance.vozvrat_order)
        return bool(getattr(vozvrat_order, "id", None))

    def _lock_product(self, product_id: int) -> Product:
        return Product.objects.select_for_update(of=("self",)).get(pk=product_id)

    def _lock_stock(self, product_id: int, sklad_id: int) -> ProductStock:
        stock, _ = ProductStock.objects.select_for_update().get_or_create(
            product_id=product_id,
            sklad_id=sklad_id,
            defaults={"count": 0}
        )
        return stock

    def _apply_stock_delta(self, *, product_id: int, sklad_id: int, delta: int):
        """
        delta > 0 => qoldiq qo‘shiladi
        delta < 0 => qoldiq ayriladi
        """
        stock = self._lock_stock(product_id, sklad_id)
        current = int(stock.count or 0)
        new_val = current + int(delta)
        if new_val < 0:
            raise serializers.ValidationError({
                "count": f"Ombor qoldig‘i manfiy bo‘lib qolyapti. Hozir: {current}, delta: {delta}."
            })
        stock.count = new_val
        stock.save(update_fields=["count", "updated_time"])

        # Product umumiy count ishlatilsa
        prod = self._lock_product(product_id)
        if prod.count is not None:
            pcur = int(prod.count or 0)
            pnew = pcur + int(delta)
            if pnew < 0:
                raise serializers.ValidationError({
                    "count": f"Product.count manfiy bo‘lib qolyapti. Hozir: {pcur}, delta: {delta}."
                })
            prod.count = pnew
            prod.save(update_fields=["count", "updated_time"])

    # ---- validation ----

    def validate(self, attrs):
        product = attrs.get("product") or getattr(self.instance, "product", None)
        sklad = attrs.get("sklad") or getattr(self.instance, "sklad", None)
        count = attrs.get("count") if "count" in attrs else getattr(self.instance, "count", None)

        if not product:
            raise serializers.ValidationError({"product": "product majburiy."})
        if not sklad:
            raise serializers.ValidationError({"sklad": "sklad majburiy."})
        if count is None:
            raise serializers.ValidationError({"count": "count majburiy."})

        self._to_int(count, "count")

        if getattr(product, "is_delete", False):
            raise serializers.ValidationError({"product": "Bu product o‘chirilgan (is_delete=True)."})

        return attrs

    # ---- update ----

    @transaction.atomic
    def update(self, instance: OrderHistoryProduct, validated_data):
        # row lock
        instance = OrderHistoryProduct.objects.select_for_update().get(pk=instance.pk)

        # eski qiymatlar
        old_product_id = instance.product_id
        old_sklad_id = instance.sklad_id
        old_count = int(instance.count or 0)
        old_is_vozvrat = bool(instance.vozvrat_order_id)

        # yangi qiymatlar
        new_product = validated_data.get("product", instance.product)
        new_sklad = validated_data.get("sklad", instance.sklad)
        new_count = self._to_int(validated_data.get("count", instance.count), "count")
        new_is_vozvrat = self._is_vozvrat(instance, validated_data)

        # sign: vozvrat => +1 (qoldiq ortadi), sale => -1 (qoldiq kamayadi)
        old_sign = 1 if old_is_vozvrat else -1
        new_sign = 1 if new_is_vozvrat else -1

        # deadlock oldini olish uchun lock tartibi (product_id bo‘yicha)
        # (sodda, lekin foydali)
        lock_pairs = [
            (old_product_id, old_sklad_id),
            (new_product.id, new_sklad.id),
        ]
        lock_pairs = sorted(set(lock_pairs), key=lambda x: (x[0], x[1]))

        # kerakli product/stocklarni lock qilib qo‘yamiz
        for pid, sid in lock_pairs:
            self._lock_product(pid)
            self._lock_stock(pid, sid)

        # 1) OLD ta’sirini rollback qilamiz
        #    old_sign * old_count avval apply bo‘lgan, rollback => -old_sign*old_count
        rollback_delta = -old_sign * old_count
        if rollback_delta != 0:
            self._apply_stock_delta(product_id=old_product_id, sklad_id=old_sklad_id, delta=rollback_delta)

        # 2) NEW apply qilishdan oldin (sale bo‘lsa) qoldiq tekshiruvi
        #    rollback’dan keyin yangi stockni tekshiramiz
        if new_sign == -1:
            stock = ProductStock.objects.select_for_update().get_or_create(
                product_id=new_product.id, sklad_id=new_sklad.id, defaults={"count": 0}
            )[0]
            available = int(stock.count or 0)
            if available < new_count:
                raise serializers.ValidationError({
                    "count": f"Qoldiq yetarli emas. Omborda: {available}, so‘raldi: {new_count}."
                })

        # 3) NEW ta’sirini apply qilamiz
        apply_delta = new_sign * new_count
        if apply_delta != 0:
            self._apply_stock_delta(product_id=new_product.id, sklad_id=new_sklad.id, delta=apply_delta)

        # 4) Endi instance update
        # Productdan FKlarni yangilab qo‘yamiz
        locked_product = self._lock_product(new_product.id)
        validated_data["branch"] = locked_product.branch
        validated_data["branch_category"] = locked_product.branch_category
        validated_data["model"] = locked_product.model
        validated_data["type"] = locked_product.type
        validated_data["size"] = locked_product.size
        validated_data["real_price"] = locked_product.real_price

        # given_count default
        if validated_data.get("given_count") is None:
            validated_data["given_count"] = new_count

        updated = super().update(instance, validated_data)
        return updated



class OrderHistoryProductVozvratCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = (
            'id', 'date',
            'order_history', 'vozvrat_order',
            'product', 'sklad',
            'branch', 'branch_category', 'model', 'type', 'size',
            'count', 'given_count', 'price_dollar', 'price_sum',
            'real_price', 'unit_price', 'wholesale_price',
            'is_delete', 'cargo_terminal',
            'price_difference', 'status_order', 'is_karzinka'
        )
        # read_only_fields = ('branch', 'model', 'type', 'size', 'real_price', 'is_delete')

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
        product_stock, _ = ProductStock.objects.select_for_update().get_or_create(
            product_id=locked_product.pk,
            sklad_id=sklad.pk,
            defaults={"count": 0}
        )

        current_stock = int(product_stock.count or 0)

        # if current_stock < order_count:
        #     raise serializers.ValidationError({
        #         "count": f"Qoldiq yetarli emas. Omborda: {current_stock}, so‘raldi: {order_count}."
        #     })

        # Productdan FKlarni ko‘chiramiz
        validated_data["branch"] = locked_product.branch
        validated_data["branch_category"] = locked_product.branch_category
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

        # 3) ProductStock oshiramiz (vozvrat)
        #    (ProductStock yo‘q bo‘lsa bu yerga kelmaydi, chunki current_stock=0 bo‘ladi va yuqorida xato qaytadi)
        product_stock.count = current_stock + order_count
        product_stock.save(update_fields=["count", "updated_time"])

        # 4) Agar Product.count ham real ishlatilsa (umumiy qoldiq):
        if locked_product.count is not None:
            locked_product.count = int(locked_product.count or 0) + order_count
            locked_product.save(update_fields=["count", "updated_time"])

        return instance




