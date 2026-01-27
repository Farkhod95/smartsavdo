from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from directory.serializers import RegionListSerializer, DistrictSerializer, CountrySerializer

from .models import User, Role, AppModule, Company


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'codename']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(style={'input_type': 'username'})
    password = serializers.CharField(style={'input_type': 'password'})


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'logo', 'email', 'phone', 'address', 'title', 'description')


class CompanyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'name', 'logo', 'email', 'phone', 'address', 'title', 'description')



class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(source='role', read_only=True)

    class Meta:
        model = User
        fields = ('id','username','full_name','is_active','date_of_birthday','gender','phone_number','email','date_joined','password','company','region','district','role','roles','address','avatar','created_time','updated_time','created_by','updated_by')
        extra_kwargs = {'username': {'validators': [UnicodeUsernameValidator(), UniqueValidator(queryset=User.objects.all())]}, 'password': {'write_only': True, 'required': False, 'allow_null': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.password = make_password(password)
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        for field in ['username','full_name','is_active','date_of_birthday','gender','phone_number','email','company','region','district','role','address','avatar','created_by','updated_by']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        password = validated_data.get('password', None)
        if password:
            instance.password = make_password(password)

        instance.save()
        return instance


class UserListPublicSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(source='role', read_only=True)
    company_detail = CompanySerializer(source='company', read_only=True)
    region_detail = RegionListSerializer(source='Company', read_only=True)
    district_detail = DistrictSerializer(source='district', read_only=True)

    class Meta:
        model = User
        fields = ('id','username','full_name','is_active','date_of_birthday','gender','phone_number','avatar','email','date_joined','role','roles','company','company_detail','region','region_detail','district','district_detail','address')



class UserListSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(source='role', read_only=True)

    class Meta:
        model = User
        fields = ('id','username','full_name','is_active','date_of_birthday','gender','phone_number','avatar','email','date_joined','role','roles','company','region','district','address')



class RelatedUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {
            'username': {
                'validators': [UnicodeUsernameValidator(), UniqueValidator(queryset=User.objects.all())],
            }
        }


class RelatedUserPutSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {
            'username': {
                'validators': [],
            }
        }


class ContentTypeSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField(method_name='get_permissions')

    class Meta:
        model = ContentType
        fields = ('id', 'model', 'permissions')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'extendedcontenttype'):
            ret['model'] = instance.extendedcontenttype.extend_name.upper()
        else:
            ret['model'] = ret['model'].upper()
        return ret

    def get_permissions(self, instance):
        permissions = Permission.objects.filter(content_type=instance.id)
        result = []
        for p in permissions:
            result.append(
                {"id": p.id, "name": p.codename.split('_')[0].upper()}
            )
        return result


class AppModuleSerializer(serializers.ModelSerializer):
    modules = ContentTypeSerializer(source='content_types', read_only=True, many=True)

    class Meta:
        model = AppModule
        fields = ('id', 'name', 'modules', 'sorting')


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def validate_old_password(self, value):
        user = self.instance
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value

    def update(self, instance, validated_data):

        instance.set_password(validated_data['password'])
        instance.save()
        return instance

