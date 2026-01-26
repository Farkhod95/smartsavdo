from django.contrib import admin
from .models import FAQ, Product, ProductImage


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order_index')
    fields = (
        'question', 'answer', 'order_index',
    )
    search_fields = ('question', 'answer')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'category', 'model', 'model_type', 'model_size',
        'size', 'type', 'count',
        'real_price', 'price',
        'sorting', 'is_delete'
    )
    fields = (
        'category', 'model', 'model_type', 'model_size',
        'size', 'type', 'count',
        'real_price', 'price',
        'sorting', 'is_delete'
    )
    search_fields = ('id',)  # Product modelida name yo‘q, shuning uchun id bilan qidirish
    list_filter = ('category', 'model', 'model_type', 'model_size', 'type', 'is_delete')
    ordering = ('sorting', 'id')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'file', 'created_time')
    fields = ('product', 'file')
    search_fields = ('product__id',)
    list_filter = ('product',)
    ordering = ('-created_time',)