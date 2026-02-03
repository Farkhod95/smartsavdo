from django.urls import re_path, path

from inventory.views.product import ProductView, ProductDetailView, ProductFieldInfoView, ProductViewList
from inventory.views.product_branch import ProductBranchView, ProductBranchDetailView, ProductBranchFieldInfoView, \
    ProductBranchViewList
from inventory.views.product_history import ProductHistoryView, ProductHistoryDetailView, ProductHistoryFieldInfoView
from inventory.views.product_image import ProductImageView, ProductImageDetailView, ProductImageFieldInfoView
from inventory.views.product_model import ProductModelView, ProductModelDetailView, ProductModelFieldInfoView
from inventory.views.product_type import ProductTypeView, ProductTypeDetailView, ProductTypeFieldInfoView
from inventory.views.product_type_size import ProductTypeSizeView, ProductTypeSizeDetailView, \
    ProductTypeSizeFieldInfoView
from inventory.views.unit import UnitView, UnitDetailView, UnitFieldInfoView

urlpatterns = [
    re_path(r'^unit$', UnitView.as_view(), name='unit_view'),
    path('unit/<int:pk>', UnitDetailView.as_view(), name='unit_detail_view'),
    path('unit/fields', UnitFieldInfoView.as_view(), name='unit_fields_info'),

    re_path(r'^product-branch$', ProductBranchView.as_view(), name='product_branch_view'),
    path('product-branch/<int:pk>', ProductBranchDetailView.as_view(), name='product_branch_detail_view'),
    path('product-branch/fields', ProductBranchFieldInfoView.as_view(), name='product_branch_fields_info'),
    path('product-branch/public', ProductBranchViewList.as_view(), name='product_branch_public_info'),

    re_path(r'^product-model$', ProductModelView.as_view(), name='product_model_view'),
    path('product-model/<int:pk>', ProductModelDetailView.as_view(), name='product_model_detail_view'),
    path('product-model/fields', ProductModelFieldInfoView.as_view(), name='product_model_fields_info'),

    re_path(r'^product-type$', ProductTypeView.as_view(), name='product_type_view'),
    path('product-type/<int:pk>', ProductTypeDetailView.as_view(), name='product_type_detail_view'),
    path('product-type/fields', ProductTypeFieldInfoView.as_view(), name='product_type_fields_info'),

    re_path(r'^product-type-size$', ProductTypeSizeView.as_view(), name='product_type_size_view'),
    path('product-type-size/<int:pk>', ProductTypeSizeDetailView.as_view(), name='product_type_size_detail_view'),
    path('product-type-size/fields', ProductTypeSizeFieldInfoView.as_view(), name='product_type_size_fields_info'),

    re_path(r'^product$', ProductView.as_view(), name='product_view'),
    path('product/<int:pk>', ProductDetailView.as_view(), name='product_detail_view'),
    path('product/fields', ProductFieldInfoView.as_view(), name='product_fields_info'),
    path('product/public', ProductViewList.as_view(), name='product_public_info'),

    re_path(r'^product-history$', ProductHistoryView.as_view(), name='product_history_view'),
    path('product-history/<int:pk>', ProductHistoryDetailView.as_view(), name='product_history_detail_view'),
    path('product-history/fields', ProductHistoryFieldInfoView.as_view(), name='product_history_fields_info'),

    re_path(r'^product-image$', ProductImageView.as_view(), name='product_image_view'),
    path('product-image/<int:pk>', ProductImageDetailView.as_view(), name='product_image_detail_view'),
    path('product-image/fields', ProductImageFieldInfoView.as_view(), name='product_image_fields_info'),
]