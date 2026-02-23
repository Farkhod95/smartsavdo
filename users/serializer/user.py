# users/serializers/common.py
from rest_framework import serializers
from users.models import User  # User modeli qayerda bo'lsa shuni yozing


class UserForSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'full_name',
            'is_active',
            'date_of_birthday',
            'gender',
            'phone_number',
            'avatar',
            'email',
        )