from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from users.models import User, Role, AppModule, Company


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'email', 'phone_number', 'gender', 'date_of_birthday', 'avatar', 'address')}),
        (_('Company & Location'), {'fields': ('filials', 'region', 'district')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'roles', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Audit'), {'fields': ('created_by', 'updated_by', 'created_time', 'updated_time')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'email', 'phone_number', 'gender', 'date_of_birthday', 'avatar', 'address', 'filials', 'region', 'district', 'roles', 'is_active', 'is_staff', 'password1', 'password2'),
        }),
    )

    list_display = ('id', 'username', 'full_name', 'phone_number', 'email', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'roles', 'filials', 'region', 'district')
    search_fields = ('username', 'full_name', 'phone_number', 'email')
    ordering = ('-id',)
    filter_horizontal = ('groups', 'user_permissions')

    readonly_fields = ('date_joined', 'last_login', 'created_time', 'updated_time')

    def is_admin(self, obj) -> bool:
        return obj.is_admin()
    is_admin.boolean = True


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo', 'email', 'phone', 'address', 'region', 'district', 'description')
    fields = ('name', 'logo', 'email', 'phone', 'address', 'region', 'district', 'description')
    search_fields = ('name',)


@admin.register(Role)
class RoleAdmin(GroupAdmin):
    list_display = ('name', 'description')
    fields = ('name', 'description', 'permissions')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)


@admin.register(AppModule)
class AppModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'on_dashboard')

