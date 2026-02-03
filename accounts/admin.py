from django.contrib import admin
from accounts.models import (
    District, Region, Country, Filial, FilialAccount, Sklad
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


@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'district', 'phone_number', 'is_active', 'is_delete')
    fields = ('name', 'region', 'district', 'address', 'phone_number', 'logo', 'is_active', 'is_delete')
    search_fields = ('name', 'phone_number')
    list_filter = ('is_active', 'is_delete', 'region', 'district')


@admin.register(FilialAccount)
class FilialAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'filial', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')
    fields = ('filial', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer')
    search_fields = ('filial__name',)
    list_filter = ('filial',)


@admin.register(Sklad)
class SkladAdmin(admin.ModelAdmin):
    list_display = ('name', 'filial', 'region', 'district', 'phone_number', 'is_active', 'is_delete')
    fields = ('name', 'filial', 'region', 'district', 'address', 'phone_number', 'is_active', 'is_delete')
    search_fields = ('name', 'phone_number', 'address', 'filial__name')
    list_filter = ('is_active', 'is_delete', 'filial', 'region', 'district')