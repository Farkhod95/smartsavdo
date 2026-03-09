from django.contrib import admin

from .models import (
    Client,
    ClientKeshbekHistory,
    Order,
    OrderHistory,
    VozvratOrder,
    OrderHistoryProduct,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'phone_number', 'telegram_id',
        'region', 'district', 'filial',
        'total_debt', 'keshbek',
        'is_active', 'is_profit_loss', 'type', 'is_delete',
    )
    search_fields = ('full_name', 'phone_number', 'telegram_id')
    list_filter = ('is_active', 'is_delete', 'filial', 'region', 'district', 'type')

    fieldsets = (
        ('Asosiy', {
            'classes': ('wide',),
            'fields': (
                ('full_name', 'phone_number'),
                ('telegram_id', 'gender'),
                ('date_of_birthday', 'type'),
                ('is_active', 'is_delete'),
            )
        }),
        ('Manzil / Filial', {
            'classes': ('wide',),
            'fields': (
                ('region', 'district'),
                ('filial',),
            )
        }),
        ('Moliyaviy', {
            'classes': ('wide',),
            'fields': (
                ('total_debt', 'keshbek'),
                ('is_profit_loss',),
            )
        }),
    )


@admin.register(ClientKeshbekHistory)
class ClientKeshbekHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'keshbek', 'keshbek_summa', 'order_history',
    )
    search_fields = ('client__full_name', 'client__phone_number')
    list_filter = ('client',)

    fieldsets = (
        ('Asosiy', {
            'classes': ('wide',),
            'fields': (
                ('client',),
                ('keshbek', 'keshbek_summa'),
                ('order_history',),
            )
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'number_of_order', 'client', 'filial', 'date_last_order',
        'all_profit_dollar', 'all_product_summa',
        'summa_total_dollar',
        'summa_dollar', 'summa_naqt', 'summa_kilik',
        'summa_terminal', 'summa_transfer',
        'total_debt_old_client', 'total_debt_client',
        'discount_amount',
        'is_delete',
    )
    search_fields = ('number_of_order', 'client__full_name', 'client__phone_number', 'filial__name')
    list_filter = ('is_delete', 'filial', 'date_last_order')

    fieldsets = (
        ('Asosiy', {
            'classes': ('wide',),
            'fields': (
                ('number_of_order', 'date_last_order'),
                ('client', 'filial'),
                ('is_delete',),
            )
        }),
        ('Hisob-kitob', {
            'classes': ('wide',),
            'fields': (
                ('all_profit_dollar', 'all_product_summa'),
                ('total_debt_old_client', 'total_debt_client'),
                ('summa_total_dollar', 'summa_dollar'),
                ('summa_naqt', 'summa_kilik'),
                ('summa_terminal', 'summa_transfer'),
                ('discount_amount',),
            )
        }),
    )


@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'order', 'client', 'order_filial', 'employee', 'currency', 'created_time', 'date',
        'exchange_rate',
        'all_product_summa', 'discount_amount',
        'summa_total_dollar', 'summa_dollar',
        'summa_naqt', 'summa_kilik',
        'summa_terminal', 'summa_transfer',
        'zdacha_dollar', 'zdacha_som',
        'total_debt_client', 'total_debt_today_client',
        'all_profit_dollar',
        'order_status', 'update_status',
        'is_debtor_product',
        'status_order_dukon', 'status_order_sklad',
        'driver_info', 'price_difference',
        'is_karzinka', 'is_delete',
    )
    search_fields = (
        'client__full_name', 'client__phone_number', 'order_filial__name',
        'employee__username', 'employee__first_name', 'employee__last_name',
        'note',
    )
    list_filter = (
        'is_delete', 'date', 'order_status', 'is_debtor_product',
        'status_order_dukon', 'status_order_sklad', 'is_karzinka',
    )

    fieldsets = (
        ('Asosiy', {
            'classes': ('wide',),
            'fields': (
                ('order', 'client', 'order_filial'),
                ('employee', 'currency', 'date'),
                ('exchange_rate',),
                ('is_delete', 'is_karzinka'),
            )
        }),
        ('To‘lovlar', {
            'classes': ('wide',),
            'fields': (
                ('all_product_summa', 'discount_amount'),
                ('summa_total_dollar', 'summa_dollar'),
                ('summa_naqt', 'summa_kilik'),
                ('summa_terminal', 'summa_transfer'),
                ('zdacha_dollar', 'zdacha_som'),
            )
        }),
        ('Qarz / Foyda', {
            'classes': ('wide',),
            'fields': (
                ('total_debt_client', 'total_debt_today_client'),
                ('all_profit_dollar',),
            )
        }),
        ('Statuslar', {
            'classes': ('wide',),
            'fields': (
                ('order_status', 'update_status', 'price_difference'),
                ('is_debtor_product',),
                ('status_order_dukon', 'status_order_sklad'),
                ('driver_info',),
            )
        }),
        ('Izoh', {
            'classes': ('wide',),
            'fields': (('note',),)
        }),
    )


@admin.register(VozvratOrder)
class VozvratOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'filial', 'client', 'employee', 'date',
        'exchange_rate',
        'old_total_debt_client', 'total_debt_client',
        'summa_total_dollar', 'summa_dollar',
        'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer',
        'discount_amount',
        'is_vazvrat_status', 'is_delete', 'is_karzinka',
    )
    search_fields = ('client__full_name', 'client__phone_number', 'filial__name', 'note')
    list_filter = ('is_delete', 'is_vazvrat_status',  'is_karzinka', 'date', 'filial')

    fieldsets = (
        ('Asosiy', {
            'classes': ('wide',),
            'fields': (
                ('filial', 'client'),
                ('employee', 'date'),
                ('exchange_rate',),
                ('is_vazvrat_status', 'is_delete',  'is_karzinka'),
            )
        }),
        ('Qaytarilgan to‘lovlar', {
            'classes': ('wide',),
            'fields': (
                ('summa_total_dollar', 'summa_dollar'),
                ('summa_naqt', 'summa_kilik'),
                ('summa_terminal', 'summa_transfer'),
                ('discount_amount',),
            )
        }),
        ('Qarz holati', {
            'classes': ('wide',),
            'fields': (
                ('old_total_debt_client', 'total_debt_client'),
            )
        }),
        ('Izoh', {
            'classes': ('wide',),
            'fields': (('note',),)
        }),
    )


@admin.register(OrderHistoryProduct)
class OrderHistoryProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'date',
        'order_history', 'vozvrat_order', 'product', 'sklad',
        'branch', 'branch_category', 'model', 'type', 'size',
        'count', 'given_count', 'price_dollar', 'price_sum',
        'real_price', 'unit_price', 'wholesale_price',
        'cargo_terminal',
        'price_difference', 'status_order',
        'is_karzinka', 'is_delete',
    )
    search_fields = (
        'cargo_terminal',
        'branch__name', 'branch_category__name', 'model__name', 'type__name', 'size__name',
    )
    list_filter = ('is_delete', 'date', 'status_order', 'price_difference', 'is_karzinka')

    fieldsets = (
        ('Asosiy', {
            'classes': ('wide',),
            'fields': (
                ('date',),
                ('order_history', 'vozvrat_order', 'product', 'sklad'),
                ('is_delete', 'is_karzinka'),
            )
        }),
        ('Mahsulot', {
            'classes': ('wide',),
            'fields': (
                ('branch', 'branch_category', 'model'),
                ('type', 'size'),
                ('cargo_terminal',),
            )
        }),
        ('Miqdor', {
            'classes': ('wide',),
            'fields': (
                ('count', 'given_count'),
                ('status_order',),
            )
        }),
        ('Narxlar', {
            'classes': ('wide',),
            'fields': (
                ('real_price', 'price_dollar', 'price_sum'),
                ( 'unit_price', 'wholesale_price', 'price_difference'),
            )
        }),
    )
