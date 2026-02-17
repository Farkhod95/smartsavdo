from django_filters import FilterSet
from inventory.models import Unit, ProductBranch, ProductModel, ProductType, ProductTypeSize, Product, ProductHistory, \
    ProductImage, ProductBranchCategory, ProductStock


class UnitFilter(FilterSet):
    class Meta:
        model = Unit
        fields = {
            'code': ['exact', 'icontains'],
            'name': ['exact', 'icontains'],
            'is_active': ['exact'],
        }


class ProductBranchFilter(FilterSet):
    class Meta:
        model = ProductBranch
        fields = {
            'name': ['exact', 'icontains'],
            'sorting': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
        }


class ProductBranchCategoryFilter(FilterSet):

    class Meta:
        model = ProductBranchCategory
        fields = ('product_branch', 'is_delete', 'name')


class ProductModelFilter(FilterSet):
    class Meta:
        model = ProductModel
        fields = {
            'name': ['exact', 'icontains'],
            'branch': ['exact'],
            'branch_category': ['exact'],
            'sorting': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
        }


class ProductTypeFilter(FilterSet):
    class Meta:
        model = ProductType
        fields = {
            'name': ['exact', 'icontains'],
            'branch': ['exact'],
            'branch_category': ['exact'],
            'madel': ['exact'],
            'sorting': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
        }


class ProductTypeSizeFilter(FilterSet):
    class Meta:
        model = ProductTypeSize
        fields = {
            'product_type': ['exact'],
            'size': ['exact', 'gte', 'lte'],
            'unit': ['exact'],
            'sorting': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
        }


class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            'date': ['exact', 'gte', 'lte'],
            'reserve_limit': ['exact', 'gte', 'lte'],
            'filial': ['exact'],
            'branch': ['exact'],
            'branch_category': ['exact'],
            'model': ['exact'],
            'type': ['exact'],
            'size': ['exact'],
            # 'count': ['exact', 'gte', 'lte'],
            # 'real_price': ['exact', 'gte', 'lte'],
            # 'unit_price': ['exact', 'gte', 'lte'],
            # 'wholesale_price': ['exact', 'gte', 'lte'],
            # 'min_price': ['exact', 'gte', 'lte'],
            'is_delete': ['exact'],
            'is_active': ['exact'],
        }


class ProductHistoryFilter(FilterSet):
    class Meta:
        model = ProductHistory
        fields = {
            'date': ['exact', 'gte', 'lte'],
            'reserve_limit': ['exact', 'gte', 'lte'],
            'filial': ['exact'],
            'sklad': ['exact'],
            'product': ['exact'],
            'purchase_invoice': ['exact'],
            'branch': ['exact'],
            'branch_category': ['exact'],
            'model': ['exact'],
            'type': ['exact'],
            'size': ['exact'],
            # 'count': ['exact', 'gte', 'lte'],
            # 'real_price': ['exact', 'gte', 'lte'],
            # 'unit_price': ['exact', 'gte', 'lte'],
            # 'wholesale_price': ['exact', 'gte', 'lte'],
            # 'min_price': ['exact', 'gte', 'lte'],
        }


class ProductImageFilter(FilterSet):
    class Meta:
        model = ProductImage
        fields = {
            'product': ['exact'],
        }


class ProductStockFilter(FilterSet):

    class Meta:
        model = ProductStock
        fields = ('product', 'sklad', 'count')