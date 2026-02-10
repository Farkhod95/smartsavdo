from django.contrib import admin
from inventory.models import Unit, ProductBranch, ProductModel, ProductType, ProductTypeSize, Product, ProductHistory, \
    ProductImage


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    fields = ('code', 'name', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)


@admin.register(ProductBranch)
class ProductBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'sorting', 'is_delete')
    fields = ('name', 'sorting', 'is_delete')
    search_fields = ('name',)
    list_filter = ('is_delete',)


@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'sorting', 'is_delete', 'elegant_id')
    fields = ('name', 'branch', 'sorting', 'is_delete', 'elegant_id')
    search_fields = ('name', 'branch__name', 'elegant_id')
    list_filter = ('is_delete', 'branch')


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'madel', 'sorting', 'is_delete', 'elegant_id')
    fields = ('name', 'madel', 'sorting', 'is_delete', 'elegant_id')
    search_fields = ('name', 'madel__name', 'elegant_id')
    list_filter = ('is_delete', 'madel')


@admin.register(ProductTypeSize)
class ProductTypeSizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_type', 'size', 'unit', 'sorting', 'is_delete', 'elegant_id')
    fields = ('product_type', 'size', 'unit', 'sorting', 'is_delete', 'elegant_id')
    search_fields = ('product_type__name', 'unit__code', 'unit__name')
    list_filter = ('is_delete', 'unit', 'product_type')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'filial', 'branch', 'model', 'type', 'size', 'count', 'unit_price', 'wholesale_price', 'min_price', 'is_delete')
    fields = ('date', 'reserve_limit', 'filial', 'branch', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note', 'is_delete')
    search_fields = ('note', 'filial__name', 'branch__name', 'model__name', 'type__name')
    list_filter = ('is_delete', 'filial', 'branch', 'model', 'type')


@admin.register(ProductHistory)
class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'product', 'filial', 'purchase_invoice', 'branch', 'model', 'type', 'size', 'count', 'unit_price', 'wholesale_price', 'min_price')
    fields = ('date', 'reserve_limit', 'product', 'filial', 'purchase_invoice', 'branch', 'model', 'type', 'size', 'count', 'real_price', 'unit_price', 'wholesale_price', 'min_price', 'note')
    search_fields = ('note', 'product__id', 'purchase_invoice__id', 'branch__name', 'model__name', 'type__name')
    list_filter = ('date', 'branch', 'model', 'type')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'file')
    fields = ('product', 'file')
    search_fields = ('file', 'product__id')
    list_filter = ('product',)