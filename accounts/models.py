from django.db import models
from django.utils.translation import gettext_lazy as _

from restapp.models import BaseModel


class Country(BaseModel):
    code = models.CharField(_('Country code'), max_length=50, null=True, blank=True, help_text=_("Mamlakat kodi"))
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Mamlakat nomi"))

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')

    def __str__(self):
        return self.name


class Region(BaseModel):
    code = models.CharField(_('Region code'), max_length=50, null=True, blank=True, help_text=_("Viloyat kodi"))
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Viloyat nomi"))
    geo_json = models.TextField(_('GeoJson'), blank=True, help_text=_("Deo json"))

    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')

    def __str__(self):
        return f"{self.name}"


class District(BaseModel):
    code = models.CharField(_('District code'), max_length=50, null=True, blank=True, help_text=_("Tuman kodi"))
    name = models.CharField(_('District name'), max_length=255, null=True, blank=True, help_text=_("Tuman nomi"))
    region = models.ForeignKey(Region, related_name='districts', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Viloyat jadvali bilan bog'lanish"))
    geo_json = models.TextField(_('GeoJson'), blank=True, help_text=_("Geo json"))

    class Meta:
        verbose_name = _('district')
        verbose_name_plural = _('districts')

    def __str__(self):
        return self.name


class Filial(BaseModel):
    name = models.CharField(_('Filial name'), max_length=255, null=True, blank=True, help_text=_("Filial nomi"))
    region = models.ForeignKey(
        Region,
        related_name='filials',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text=_("Viloyat jadvali bilan bog'lanish")
    )
    district = models.ForeignKey(
        District,
        related_name='filials',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text=_("Tuman jadvali bilan bog'lanish")
    )
    address = models.TextField(_('Address'), null=True, blank=True, help_text=_("Manzil"))
    phone_number = models.CharField(_('Phone number'), max_length=64, null=True, blank=True, help_text=_("Telefon raqam"))
    logo = models.ImageField(upload_to='filial/logo/%Y/%m/%d', null=True, blank=True, verbose_name=_('Logo'),
                             help_text=_("Filial logotipi (ixtiyoriy)"))

    is_active = models.BooleanField(default=True, help_text=_("Is active?"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('filial')
        verbose_name_plural = _('filials')

    def __str__(self):
        return self.name or f"Filial #{self.pk}"



class FilialAccount(BaseModel):
    filial = models.ForeignKey(Filial, related_name='filial_accounts', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial jadvali bilan bog'lanish"))
    summa_total_dollar = models.DecimalField(_('Total (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Filialdagi hamma summa dollar ko'rinishida"))
    summa_dollar = models.DecimalField(_('Dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("Filialdagi summa dollarda"))
    summa_naqt = models.DecimalField(_('Cash'), max_digits=20, decimal_places=2, default=0, help_text=_("Filialdagi summa naqtda"))
    summa_kilik = models.DecimalField(_('Debt/Click'), max_digits=20, decimal_places=2, default=0, help_text=_("Filialdagi summa kilikda"))
    summa_terminal = models.DecimalField(_('Terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("Filialdagi summa terminalda"))
    summa_transfer = models.DecimalField(_('Transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("Filialdagi summa transferda"))

    class Meta:
        verbose_name = _('filial account')
        verbose_name_plural = _('filial accounts')

    def __str__(self):
        return f"{self.filial} | Account #{self.pk}" if self.filial else f"FilialAccount #{self.pk}"


class Sklad(BaseModel):
    sorting = models.IntegerField(_('Sorting'), help_text=_("Sorting"))
    name = models.CharField(_('Warehouse name'), max_length=255, null=True, blank=True, help_text=_("Sklad nomi"))
    filial = models.ForeignKey(Filial, related_name='sklads', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial jadvali bilan bog'lanish"))
    region = models.ForeignKey(Region, related_name='sklads', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Viloyat jadvali bilan bog'lanish"))
    district = models.ForeignKey(District, related_name='sklads', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Tuman jadvali bilan bog'lanish"))
    address = models.TextField(_('Address'), null=True, blank=True, help_text=_("Manzil"))
    phone_number = models.CharField(_('Phone number'), max_length=64, null=True, blank=True, help_text=_("Telefon raqam"))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Sklad')
        verbose_name_plural = _('Sklads')

    def __str__(self):
        return self.name or f"Warehouse #{self.pk}"
