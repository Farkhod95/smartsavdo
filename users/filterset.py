from django_filters.rest_framework import FilterSet

from users.models import User, Company


class UserFilter(FilterSet):

    class Meta:
        model = User
        fields = {
            'username': ['exact', 'startswith', 'contains'],
            'last_name': ['exact'],
            'first_name': ['exact'],
            'gender': ['exact'],
            'role': ['exact'],
        }


class CompanyFilter(FilterSet):

    class Meta:
        model = Company
        fields = {
            'name': ['exact'],
            'title': ['exact'],
        }

