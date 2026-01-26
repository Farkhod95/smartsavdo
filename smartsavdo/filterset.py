from django_filters.rest_framework import FilterSet
from django_filters import rest_framework as filters

from smartsavdo.models import FAQ, Product, ProductImage


class FAQFilter(FilterSet):
    order_index__gte = filters.NumberFilter(field_name='order_index', lookup_expr='gte')
    order_index__lte = filters.NumberFilter(field_name='order_index', lookup_expr='lte')

    class Meta:
        model = FAQ
        fields = {
            'id': ['exact'],
            'question': ['exact', 'icontains'],
            'order_index': ['exact'],
        }


class ProductFilter(FilterSet):

    class Meta:
        model = Product
        fields = {
            'category': ['exact'],
            'model': ['exact'],
            'model_type': ['exact'],
            'model_size': ['exact'],
            'size': ['exact'],
            'type': ['exact'],
            'sorting': ['exact'],
            'is_delete': ['exact'],
        }


class ProductImageFilter(FilterSet):

    class Meta:
        model = ProductImage
        fields = {
            'product': ['exact'],
        }