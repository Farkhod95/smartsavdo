from django.urls import re_path, path

from .views.country import CountryView, CountryDetailView, CountryFieldInfoView
from .views.district import DistrictView, DistrictDetailView, DistrictFieldInfoView, DistrictViewList
from .views.filial import FilialView, FilialDetailView, FilialFieldInfoView
from .views.filial_account import FilialAccountView, FilialAccountDetailView, FilialAccountFieldInfoView
from .views.import_country import CountryFileImportView
from .views.region import RegionView, RegionDetailView, RegionFieldInfoView, RegionViewList
from .views.sklad import SkladView, SkladDetailView, SkladFieldInfoView

urlpatterns = [
    re_path(r'^country$', CountryView.as_view(), name='country_view'),
    path('country/<int:pk>', CountryDetailView.as_view(), name='country_detail_view'),
    path('country/fields/', CountryFieldInfoView.as_view(), name='country_fields_info'),
    path("country/import-from-file/", CountryFileImportView.as_view(),
             name="country-import-from-file"),

    re_path(r'^region$', RegionView.as_view(), name='regions_view'),
    path('region/<int:pk>', RegionDetailView.as_view(), name='region_detail_view'),
    path('region/fields', RegionFieldInfoView.as_view(), name='region_fields_info'),
    re_path(r'^region/telegram', RegionViewList.as_view(), name='regions_public_view'),

    re_path(r'^district$', DistrictView.as_view(), name='districts_view'),
    path('district/<int:pk>', DistrictDetailView.as_view(), name='districts_detail_view'),
    path('district/fields', DistrictFieldInfoView.as_view(), name='district_fields_info'),
    re_path(r'^district/telegram', DistrictViewList.as_view(), name='district_public_view'),

    re_path(r'^filial$', FilialView.as_view(), name='filials_view'),
    path('filial/<int:pk>', FilialDetailView.as_view(), name='filials_detail_view'),
    path('filial/fields', FilialFieldInfoView.as_view(), name='filial_fields_info'),

    re_path(r'^filial-account$', FilialAccountView.as_view(), name='filial_account_view'),
    path('filial-account/<int:pk>', FilialAccountDetailView.as_view(), name='filial_account_detail_view'),
    path('filial-account/fields', FilialAccountFieldInfoView.as_view(), name='filial_account_fields_info'),

    re_path(r'^sklad$', SkladView.as_view(), name='sklad_view'),
    path('sklad/<int:pk>', SkladDetailView.as_view(), name='sklad_detail_view'),
    path('sklad/fields', SkladFieldInfoView.as_view(), name='sklad_fields_info'),

]