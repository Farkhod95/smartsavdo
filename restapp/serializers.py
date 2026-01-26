from rest_framework import serializers
from .models import TranslationTerm, ModelAudit


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationTerm
        fields = ('id', 'term_name', 'name_en', 'name_uz', 'name_ru', 'name_lt')
        extra_kwargs = {
            'term_name': {"required": True},
            'name_en': {"required": True},
            'name_uz': {"required": True},
            'name_ru': {"required": True},
            'name_lt': {"required": True},
        }



class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationTerm
        fields = ('term_name', 'name')


class ModelAuditSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(method_name='get_username')

    class Meta:
        model = ModelAudit
        fields = ('id', 'user', 'instance', 'instance_id', 'field_name', 'old_value', 'new_value', 'data', 'action',
                  'timestamp')

    def get_username(self, instance):
        return instance.user.username if instance.user else ''
