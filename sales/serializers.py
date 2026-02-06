from rest_framework import serializers

from accounts.serializers import RegionListSerializer, DistrictListPublicSerializer, FilialListSerializer
from inventory.serializers import ProductBranchListSerializer, ProductModelListSerializer, ProductTypeListSerializer, \
    ProductTypeSizeListSerializer
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
    vozvrat_order_detail = VozvratOrderSerializer(source='vozvrat_order', read_only=True)
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    model_detail = ProductModelListSerializer(source='model', read_only=True)
    type_detail = ProductTypeListSerializer(source='type', read_only=True)
    size_detail = ProductTypeSizeListSerializer(source='size', read_only=True)

    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'order_history_detail', 'vozvrat_order', 'vozvrat_order_detail', 'branch', 'branch_detail', 'model', 'model_detail', 'type', 'type_detail', 'size', 'size_detail', 'count', 'given_count', 'real_price', 'unit_price', 'wholesale_price', 'is_delete', 'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka')


class OrderHistoryProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistoryProduct
        fields = ('id', 'date', 'order_history', 'vozvrat_order', 'branch', 'model', 'type', 'size', 'count', 'given_count', 'real_price', 'unit_price', 'wholesale_price', 'is_delete', 'cargo_terminal', 'price_difference', 'status_order', 'is_karzinka')

