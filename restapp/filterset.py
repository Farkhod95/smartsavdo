from django_filters.rest_framework import FilterSet

from restapp.models import ModelAudit


class ModelAuditFilter(FilterSet):

    class Meta:
        model = ModelAudit
        fields = ['module', 'instance', 'instance_id']