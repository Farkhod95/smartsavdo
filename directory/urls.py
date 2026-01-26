from django.urls import re_path, path

from .views.country import CountryView, CountryDetailView, CountryFieldInfoView
from .views.district import DistrictView, DistrictDetailView, DistrictFieldInfoView
from .views.import_country import CountryFileImportView
from .views.model_size import ModelSizeView, ModelSizeDetailView, ModelSizeFieldInfoView
from .views.model_type import ModelTypeView, ModelTypeDetailView, ModelTypeFieldInfoView
from .views.product_model import ModelView, ModelDetailView, ModelFieldInfoView
from .views.product_category import ProductCategoryView, ProductCategoryDetailView, ProductCategoryFieldInfoView
from .views.region import RegionView, RegionDetailView, RegionFieldInfoView

urlpatterns = [
    re_path(r'^country$', CountryView.as_view(), name='country_view'),
    path('country/<int:pk>', CountryDetailView.as_view(), name='country_detail_view'),
    path('country/fields/', CountryFieldInfoView.as_view(), name='country_fields_info'),
    path("country/import-from-file/", CountryFileImportView.as_view(),
             name="country-import-from-file"),

    re_path(r'^region$', RegionView.as_view(), name='regions_view'),
    path('region/<int:pk>', RegionDetailView.as_view(), name='region_detail_view'),
    path('region/fields/', RegionFieldInfoView.as_view(), name='region_fields_info'),

    re_path(r'^district$', DistrictView.as_view(), name='districts_view'),
    path('district/<int:pk>', DistrictDetailView.as_view(), name='districts_detail_view'),
    path('district/fields/', DistrictFieldInfoView.as_view(), name='district_fields_info'),

    re_path(r'^product-category$', ProductCategoryView.as_view(), name='product-category-view'),
    path('product-category/<int:pk>', ProductCategoryDetailView.as_view(), name='product-category-detail-view'),
    path('product-category/fields/', ProductCategoryFieldInfoView.as_view(), name='product-category-fields-info'),

    re_path(r'^model$', ModelView.as_view(), name='model-view'),
    path('model/<int:pk>', ModelDetailView.as_view(), name='model-detail-view'),
    path('model/fields/', ModelFieldInfoView.as_view(), name='model-fields-info'),

    re_path(r'^model-type$', ModelTypeView.as_view(), name='model-type-view'),
    path('model-type/<int:pk>', ModelTypeDetailView.as_view(), name='model-type-detail-view'),
    path('model-type/fields/', ModelTypeFieldInfoView.as_view(), name='model-type-fields-info'),

    re_path(r'^model-size$', ModelSizeView.as_view(), name='model-size-view'),
    path('model-size/<int:pk>', ModelSizeDetailView.as_view(), name='model-size-detail-view'),
    path('model-size/fields/', ModelSizeFieldInfoView.as_view(), name='model-size-fields-info'),
]