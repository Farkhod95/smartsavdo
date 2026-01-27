from django.contrib import admin
from directory.models import (
    District, Region, Country, ProductCategory, Model, ModelType, ModelSize
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    fields = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    fields = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'region')
    fields = ('name', 'code', 'region', 'geo_json')
    search_fields = ('name', 'code')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sorting', 'is_delete')
    fields = ('name', 'sorting', 'is_delete')
    search_fields = ('name',)
    list_filter = ('is_delete',)
    ordering = ('sorting', 'id')


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sorting', 'is_delete')
    fields = ('name', 'categories', 'sorting', 'is_delete')
    search_fields = ('name',)
    list_filter = ('is_delete',)
    ordering = ('sorting', 'id')


@admin.register(ModelType)
class ModelTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'model', 'sorting', 'is_delete')
    fields = ('name', 'model', 'sorting', 'is_delete')
    search_fields = ('name',)
    list_filter = ('model', 'is_delete')
    ordering = ('sorting', 'id')


@admin.register(ModelSize)
class ModelSizeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'model_type',
        'size', 'type', 'sorting', 'is_delete'
    )
    fields = (
        'model_type',
        'size', 'type', 'sorting', 'is_delete'
    )
    list_filter = ('model_type', 'type', 'is_delete')
    ordering = ('sorting', 'id')