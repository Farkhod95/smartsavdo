from django.urls import re_path, path

from users.view.company import CompanyView, CompanyDetailView, CompanyFieldInfoView
from users.view.enums import UserGenderList
from users.view.role import RoleView, RolePermissionGridView, RoleDetailView
from users.view.user import UserView, UserDetailView, UserListView


urlpatterns = [
    re_path(r'^user$', UserView.as_view(), name='user_view'),
    path('user/<int:pk>', UserDetailView.as_view(), name='user_detail_view'),

    re_path(r'^user-view$', UserListView.as_view(), name='userlist_view'),

    re_path(r'^role$', RoleView.as_view(), name='roles_view'),
    path('role/<int:pk>', RoleDetailView.as_view(), name='roles_details_view'),
    re_path(r'^role/grid$', RolePermissionGridView.as_view(), name='roles_grid'),

    re_path(r'^company', CompanyView.as_view(), name='company_view'),
    path('company/<int:pk>', CompanyDetailView.as_view(), name='company_detail_view'),
    path('company/fields', CompanyFieldInfoView.as_view(), name='company_fields_info'),

    # Enums api
    re_path(r'^user/enum/gender$', UserGenderList.as_view(), name='roles_view'),
]
