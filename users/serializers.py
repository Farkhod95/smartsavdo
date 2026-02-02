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
        fields = ('id', 'name', 'logo', 'email', 'phone', 'address', 'region', 'district', 'description')


class CompanyListSerializer(serializers.ModelSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictSerializer(source='district', read_only=True)

    class Meta:
        model = Company
        fields = ('id', 'name', 'logo', 'email', 'phone', 'address', 'region', 'district', 'description')



class UserSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        required=False
    )

    companies = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = User
        fields = ('id','username','full_name','is_active','date_of_birthday','gender','phone_number','email','date_joined','password','companies','region','distric','roles','address','avatar','created_time','updated_time','created_by','updated_by')
        extra_kwargs = {'username': {'validators': [UnicodeUsernameValidator(), UniqueValidator(queryset=User.objects.all())]}, 'password': {'write_only': True, 'required': False, 'allow_null': True}}

    def create(self, validated_data):
        # ManyToMany va parolni alohida olib qo'yamiz
        companies = validated_data.pop('companies', [])
        roles_ids = validated_data.pop('roles', [])
        password = validated_data.pop('password', None)

        user = User(**validated_data)

        if password:
            # istasang validate_password(password) ham qo'shsa bo'ladi
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.is_active = True
        user.save()

        if companies:
            user.companies.set(companies)

        if roles_ids:
            user.roles.set(roles_ids)

        return user

    def update(self, instance, validated_data):
        # ManyToMany maydon va parolni alohida ajratamiz
        companies = validated_data.pop('companies', None)
        roles_ids = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)

        # Oddiy fieldlarni umumiy tarzda set qilamiz
        for attr, value in validated_data.items():
            # date_joined va boshqa read_only fieldlar Meta.read_only_fields orqali himoyalangan
            setattr(instance, attr, value)

        # Parol bo‘lsa, hash qilib saqlaymiz
        if password:
            instance.set_password(password)

        instance.save()

        # ManyToMany yangilash:
        # Agar `companies` keldi -> to‘liq yangidan set qilamiz
        # Agar kelmasa -> umuman tegmaymiz
        if companies is not None:
            instance.companies.set(companies)

        if roles_ids is not None:
            instance.roles.set(roles_ids)

        return instance


class UserListPublicSerializer(serializers.ModelSerializer):
    region_detail = RegionListSerializer(source='region', read_only=True)
    district_detail = DistrictSerializer(source='district', read_only=True)
    companies_detail = CompanyListSerializer(source='companies', many=True, read_only=True)
    roles_detail = RoleSerializer(source='roles', many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id','username','full_name','is_active','date_of_birthday','gender','phone_number','avatar','email','date_joined', 'roles', 'roles_detail','companies','companies_detail','region','region_detail','district','district_detail','address')



class UserListSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='roles', many=True, read_only=True)
    companies_detail = CompanyListSerializer(source='companies', many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id','username','full_name','is_active','date_of_birthday','gender','phone_number','avatar','email','date_joined', 'roles', 'role_detail','companies', 'companies_detail','region','district','address')



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

