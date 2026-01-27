from django_filters.rest_framework import FilterSet

from directory.models import District, Region, Country, ProductCategory, Model, ModelType, ModelSize


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


class ProductCategoryFilter(FilterSet):

    class Meta:
        model = ProductCategory
        fields = {
            'name': ['exact'],
            'sorting': ['exact'],
            'is_delete': ['exact'],
        }


class ModelFilter(FilterSet):

    class Meta:
        model = Model
        fields = {
            'name': ['exact'],
            'sorting': ['exact'],
            'is_delete': ['exact'],
            'categories': ['exact'],
        }


class ModelTypeFilter(FilterSet):

    class Meta:
        model = ModelType
        fields = {
            'name': ['exact'],
            'sorting': ['exact'],
            'is_delete': ['exact'],
            'model': ['exact'],
        }


class ModelSizeFilter(FilterSet):

    class Meta:
        model = ModelSize
        fields = {
            'sorting': ['exact'],
            'is_delete': ['exact'],
            'model_type': ['exact'],
        }