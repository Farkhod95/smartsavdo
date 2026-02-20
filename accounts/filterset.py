from django_filters.rest_framework import FilterSet

from accounts.models import District, Region, Country, Filial, FilialAccount, Sklad, Currency


class DistrictFilter(FilterSet):

    class Meta:
        model = District
        fields = {
            'code': ['exact'],
            'region': ['exact'],
        }


class CountrysFilter(FilterSet):

    class Meta:
        model = Country
        fields = {
            'name': ['exact'],
            'code': ['exact'],
        }


class RegionssFilter(FilterSet):

    class Meta:
        model = Region
        fields = {
            'name': ['exact'],
            'code': ['exact'],
        }


class FilialFilter(FilterSet):
    class Meta:
        model = Filial
        fields = {
            'name': ['exact', 'icontains'],
            'region': ['exact'],
            'district': ['exact'],
            'phone_number': ['exact', 'icontains'],
            'is_active': ['exact'],
            'is_delete': ['exact'],
            'is_head_office': ['exact'],
        }


class FilialAccountFilter(FilterSet):
    class Meta:
        model = FilialAccount
        fields = {
            'filial': ['exact'],
            'summa_total_dollar': ['exact', 'gte', 'lte'],
            'summa_dollar': ['exact', 'gte', 'lte'],
            'summa_naqt': ['exact', 'gte', 'lte'],
            'summa_kilik': ['exact', 'gte', 'lte'],
            'summa_terminal': ['exact', 'gte', 'lte'],
            'summa_transfer': ['exact', 'gte', 'lte'],
        }


class SkladFilter(FilterSet):
    class Meta:
        model = Sklad
        fields = {
            'name': ['exact', 'icontains'],
            'sorting': ['exact'],
            'filial': ['exact'],
            'region': ['exact'],
            'district': ['exact'],
            'phone_number': ['exact', 'icontains'],
            'is_active': ['exact'],
            'is_delete': ['exact'],
        }


class CurrencyFilter(FilterSet):

    class Meta:
        model = Currency
        fields = {
            'name': ['exact', 'icontains'],
            'code': ['exact'],
        }