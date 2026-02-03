from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, GroupManager
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token


class CommonInfo(models.Model):
    created_time = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_time = models.DateTimeField(auto_now_add=False, auto_now=True)


class Role(Group):
    objects = GroupManager()
    description = models.CharField(max_length=255)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')


class Company(models.Model):
    name = models.CharField(_('Kompaniya nomi'), max_length=150, default='Optivora', null=True, blank=True, help_text=_('Kompaniya to‘liq nomi'))  # Masalan: Optivora
    logo = models.ImageField(upload_to='company/logo/%Y/%m/', null=True, blank=True, verbose_name=_('Logo'), help_text=_('Kompaniya logotipi (ixtiyoriy)'))  # PNG/SVG/JPG
    email = models.EmailField(_('Email'), max_length=254, null=True, blank=True, help_text=_('Rasmiy aloqa e-pochtasi'))  # info@...
    phone = models.CharField(_('Telefon'), max_length=64, null=True, blank=True, help_text=_('Aloqa uchun telefon raqami'))  # +998...
    address = models.CharField(_('Manzil'), max_length=255, null=True, blank=True, help_text=_('Ofis manzili, shahar va mamlakat bilan'))  # Tashkent, Uzbekistan
    description = models.TextField(_('Tavsif'), null=True, blank=True,
                                   help_text=_('Kompaniya haqida batafsil tavsif (ixtiyoriy)'))  # SEO/Detail
    region = models.ForeignKey("accounts.Region", related_name='company_region', on_delete=models.SET_NULL, null=True,
                               help_text=_("Viloyat"))
    district = models.ForeignKey("accounts.District", related_name='company_district', on_delete=models.SET_NULL,
                                 null=True, help_text=_("Tuman"))
    created_time = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan vaqt"))
    updated_time = models.DateTimeField(auto_now=True, help_text=_("Yangilangan vaqt"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='companies_created', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yaratgan foydalanuvchi"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='companies_updated', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yangilagan foydalanuvchi"))

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Company')

    def __str__(self):
        return self.name


class User(AbstractUser):
    class GENDERS(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')

    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True, help_text=_("Telegram ID"))
    username = models.CharField(max_length=255, unique=True, help_text=_("Foydalanuvchi nomi"))
    full_name = models.CharField( max_length=100, help_text=_("FIO"))
    is_active = models.BooleanField(_('Active'), default=True, help_text=_("Foydalanuvchi holati"))
    date_of_birthday = models.DateField(_('date of birthday'), null=True, blank=True, help_text=_("Tug‘ilgan sanasi"))
    gender = models.CharField(choices=GENDERS.choices, max_length=6, null=True, blank=True, help_text=_("Jinsi"))
    phone_number = models.CharField(_("Phone number"), max_length=100, help_text=_("Telefon raqami"))
    email = models.EmailField(_('email address'), blank=True, null=True, help_text=_("Email manzili"))
    date_joined = models.DateTimeField(_('Date joined'), auto_now_add=True, help_text=_("Ro‘yxatdan o‘tgan sana"))
    password = models.CharField(max_length=255, null=True, blank=True, help_text=_("Parol"))
    companies = models.ManyToManyField('users.Company', blank=True, related_name='user_company',
                                       verbose_name=_('Kompaniya'))
    region = models.ForeignKey("accounts.Region", related_name='user_region', on_delete=models.SET_NULL, null=True,
                               help_text=_("Viloyat"))
    district = models.ForeignKey("accounts.District", related_name='user_district', on_delete=models.SET_NULL,
                                 null=True, help_text=_("Tuman"))
    roles = models.ManyToManyField(Role, related_name='users', blank=True, help_text=_("Foydalanuvchi rollari"))
    address = models.TextField(_("Address"), null=True, help_text=_("Yashash manzili"))
    created_time = models.DateTimeField(auto_now_add=True, help_text=_("Yaratilgan vaqt"))
    updated_time = models.DateTimeField(auto_now=True, help_text=_("Yangilangan vaqt"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='users_created', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yaratgan foydalanuvchi"))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='users_updated', null=True,
                                   on_delete=models.SET_NULL, help_text=_("Yangilagan foydalanuvchi"))
    avatar = models.ImageField(upload_to='avatars/%Y/%m/%d', null=True, blank=True, help_text=_("Profil rasmi"))

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        if self.full_name:
            return self.full_name
        return str(self.pk)

    def is_admin(self) -> bool:
        return self.role and self.role.name == 'Administrator'


class AppModule(models.Model):
    name = models.CharField(_('Module name'), max_length=125, blank=True)
    on_dashboard = models.BooleanField(default=False)
    content_types = models.ManyToManyField(ContentType)
    sorting = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = _('module')
        verbose_name_plural = _('modules')
