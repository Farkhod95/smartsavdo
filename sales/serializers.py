from rest_framework import serializers
from decimal import Decimal
from django.db import transaction

from accounts.serializers import RegionListSerializer, DistrictListPublicSerializer, FilialListSerializer
from inventory.serializers import ProductBranchListSerializer, ProductModelListSerializer, ProductTypeListSerializer, \
    ProductTypeSizeListSerializer, ProductSerializer
from sales.models import Client, ClientKeshbekHistory, Order, OrderHistory, OrderHistoryProduct, VozvratOrder


class ClientListSerializer(serializers.ModelSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictListPublicSerializer(source='district', read_only=True)
    filial_detail = FilialListSerializer(source='filial', read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'telegram_id', 'full_name', 'is_active', 'date_of_birthday', 'gender', 'phone_number', 'region', 'region_detail', 'district', 'district_detail', 'filial', 'filial_detail', 'total_debt', 'keshbek', 'is_profit_loss', 'type', 'is_delete')


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'telegram_id', 'full_name', 'is_active', 'date_of_birthday', 'gender', 'phone_number', 'region', 'district', 'filial', 'total_debt', 'keshbek', 'is_profit_loss', 'type', 'is_delete')


class ClientKeshbekHistoryListSerializer(serializers.ModelSerializer):
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = ClientKeshbekHistory
        fields = ('id', 'client', 'client_detail', 'keshbek', 'keshbek_summa', 'order_history')


class ClientKeshbekHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientKeshbekHistory
        fields = ('id', 'client', 'keshbek', 'keshbek_summa', 'order_history')


class OrderListSerializer(serializers.ModelSerializer):
    client_detail = ClientListSerializer(source='client', read_only=True)
    filial_detail = FilialListSerializer(source='filial', read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'number_of_order', 'client', 'client_detail', 'filial', 'filial_detail', 'date_last_order', 'all_profit_dollar', 'total_debt_client', 'total_debt_old_client', 'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete')


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'number_of_order', 'client', 'filial', 'date_last_order', 'all_profit_dollar', 'total_debt_client', 'total_debt_old_client', 'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete')


class OrderHistoryListSerializer(serializers.ModelSerializer):
    order_detail = OrderListSerializer(source='order', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = OrderHistory
        fields = ('id', 'order', 'order_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date', 'note', 'all_profit_dollar', 'total_debt_client', 'total_debt_today_client', 'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status', 'is_debtor_product', 'status_order_dukon', 'status_order_sklad', 'driver_info', 'is_karzinka')


def d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def recompute_order_totals(order: Order) -> Order:
    """
    Shu Orderga bog'langan (is_delete=False) OrderHistory lar ichidan
    FAQAT is_karzinka=False bo'lganlarini hisobga oladi.
    """
    qs = order.order_histories.filter(is_delete=False, is_karzinka=False).order_by("id")

    if not qs.exists():
        order.number_of_order = 0
        order.date_last_order = None
        order.all_profit_dollar = Decimal("0")
        order.total_debt_client = Decimal("0")
        order.total_debt_old_client = Decimal("0")
        order.all_product_summa = Decimal("0")

        order.summa_total_dollar = Decimal("0")
        order.summa_dollar = Decimal("0")
        order.summa_naqt = Decimal("0")
        order.summa_kilik = Decimal("0")
        order.summa_terminal = Decimal("0")
        order.summa_transfer = Decimal("0")
        order.discount_amount = Decimal("0")
        order.save()
        return order

    last_h = qs.last()

    total_profit = Decimal("0")
    total_product_summa = Decimal("0")

    total_paid_total_dollar = Decimal("0")
    total_paid_dollar = Decimal("0")
    total_paid_naqt = Decimal("0")
    total_paid_kilik = Decimal("0")
    total_paid_terminal = Decimal("0")
    total_paid_transfer = Decimal("0")
    total_discount = Decimal("0")

    for h in qs:
        total_profit += d(h.all_profit_dollar)
        total_product_summa += d(h.all_product_summa)

        total_paid_total_dollar += d(h.summa_total_dollar)
        total_paid_dollar += d(h.summa_dollar)
        total_paid_naqt += d(h.summa_naqt)
        total_paid_kilik += d(h.summa_kilik)
        total_paid_terminal += d(h.summa_terminal)
        total_paid_transfer += d(h.summa_transfer)
        total_discount += d(h.discount_amount)

    total_debt_client = d(last_h.total_debt_client)
    today_debt = d(last_h.total_debt_today_client)
    old_debt = total_debt_client - today_debt
    if old_debt < 0:
        old_debt = Decimal("0")

    order.number_of_order = qs.count()
    order.client = last_h.client or order.client
    order.date_last_order = last_h.date

    order.all_profit_dollar = total_profit
    order.all_product_summa = total_product_summa

    order.summa_total_dollar = total_paid_total_dollar
    order.summa_dollar = total_paid_dollar
    order.summa_naqt = total_paid_naqt
    order.summa_kilik = total_paid_kilik
    order.summa_terminal = total_paid_terminal
    order.summa_transfer = total_paid_transfer

    order.discount_amount = total_discount
    order.total_debt_client = total_debt_client
    order.total_debt_old_client = old_debt

    order.save()
    return order


class OrderHistoryUpdateSerializer(serializers.ModelSerializer):
    """
    - Filial doim request.user.order_filial dan olinadi.
    - Order create/update HISOB-KITOB faqat is_karzinka=False bo'lganda ishlaydi.
    """

    class Meta:
        model = OrderHistory
        fields = (
            'id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'all_profit_dollar', 'total_debt_client', 'total_debt_today_client',
            'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt',
            'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
            'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
            'is_debtor_product', 'status_order_dukon', 'status_order_sklad',
            'driver_info', 'is_karzinka'
        )
        extra_kwargs = {
            "order": {"read_only": True},
            "employee": {"required": False, "allow_null": True},
        }

    def _get_user_filial(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        filial = getattr(user, "order_filial", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Autentifikatsiya talab qilinadi."})

        if filial is None:
            raise serializers.ValidationError({
                "detail": "Sizga order_filial biriktirilmagan. (User.order_filial = null)"
            })

        return filial

    def _is_karzinka_false(self, validated_data, instance=None) -> bool:
        """
        Create: validated_data['is_karzinka'] default True (model default).
        Update: agar request yubormasa, instancedan olamiz.
        """
        if "is_karzinka" in validated_data:
            return validated_data.get("is_karzinka") is False
        if instance is not None:
            return instance.is_karzinka is False
        # create bo'lsa va yuborilmasa model default True, demak ishlamasin
        return False

    @transaction.atomic
    def create(self, validated_data):
        # employee bo'sh kelsa -> user
        request = self.context.get("request")
        if validated_data.get("employee") is None and request and request.user.is_authenticated:
            validated_data["employee"] = request.user

        # Avval OrderHistory ni yaratamiz
        instance = super().create(validated_data)

        # Faqat is_karzinka=False bo'lsa Orderga tegamiz
        if instance.is_karzinka is False:
            client = instance.client
            if client is None:
                raise serializers.ValidationError({"client": "client majburiy"})

            filial = self._get_user_filial()

            order, _created = Order.objects.get_or_create(
                client=client,
                filial=filial,
                defaults={
                    "date_last_order": instance.date,
                    "is_delete": False,
                }
            )

            # history ni orderga bog'laymiz
            instance.order = order
            instance.save(update_fields=["order"])

            # totals
            recompute_order_totals(order)

        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        if validated_data.get("employee") is None and request and request.user.is_authenticated:
            validated_data["employee"] = request.user

        updated_instance = super().update(instance, validated_data)

        # Faqat is_karzinka=False bo'lsa Orderga tegamiz
        if updated_instance.is_karzinka is False:
            client = updated_instance.client
            if client is None:
                raise serializers.ValidationError({"client": "client majburiy"})

            filial = self._get_user_filial()

            order, _created = Order.objects.get_or_create(
                client=client,
                filial=filial,
                defaults={
                    "date_last_order": updated_instance.date,
                    "is_delete": False,
                }
            )

            # history ni orderga bog'laymiz
            if updated_instance.order_id != order.id:
                updated_instance.order = order
                updated_instance.save(update_fields=["order"])

            recompute_order_totals(order)

        return updated_instance


class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = ('id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note', 'all_profit_dollar', 'total_debt_client', 'total_debt_today_client', 'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status', 'is_debtor_product', 'status_order_dukon', 'status_order_sklad', 'driver_info', 'is_karzinka')


class VozvratOrderListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete', 'is_vazvrat_status')


class VozvratOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete', 'is_vazvrat_status')


class OrderHistoryProductListSerializer(serializers.ModelSerializer):
    order_history_detail = OrderHistoryListSerializer(source='order_history', read_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)
    vozvrat_order_detail = VozvratOrderSerializer(source='vozvrat_order', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'order_history_detail', 'vozvrat_order', 'vozvrat_order_detail', 'product', 'product_detail', 'branch', 'branch_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'given_count', 'real_price', 'unit_price', 'wholesale_price', 'is_delete', 'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka')


class OrderHistoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'vozvrat_order', 'product', 'branch', 'model', 'type', 'size', 'count', 'given_count', 'real_price', 'unit_price', 'wholesale_price', 'is_delete', 'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka')

