from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
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

    is_head_office = models.BooleanField(default=True, help_text=_("Is head office?"))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('filial')
        verbose_name_plural = _('filials')

        indexes = [
            models.Index(fields=["is_delete", "is_active"]),
            models.Index(fields=["region", "district", "is_delete"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["is_head_office", "is_delete"]),
        ]

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

        indexes = [
            models.Index(fields=["filial"]),
        ]

    def __str__(self):
        return f"{self.filial} | Account #{self.pk}" if self.filial else f"FilialAccount #{self.pk}"


class Sklad(BaseModel):
    sorting = models.IntegerField(_('Sorting'), help_text=_("Sorting"))
    name = models.CharField(_('Warehouse name'), max_length=255, null=True, blank=True, help_text=_("Sklad nomi"))
    filial = models.ForeignKey(
        Filial, related_name='sklads', on_delete=models.SET_NULL,
        null=True, blank=True, help_text=_("Filial jadvali bilan bog'lanish")
    )
    region = models.ForeignKey(Region, related_name='sklads', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, related_name='sklads', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.TextField(_('Address'), null=True, blank=True)
    phone_number = models.CharField(_('Phone number'), max_length=64, null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Sklad')
        verbose_name_plural = _('Sklads')
        constraints = [
            # Faqat o‘chirilmaganlarda unique bo‘lsin desangiz:
            models.UniqueConstraint(
                fields=['filial', 'sorting'],
                condition=Q(is_delete=False),
                name='uniq_sklad_sorting_per_filial_not_deleted'
            ),
        ]

        indexes = [
            models.Index(fields=["filial", "is_delete", "is_active"]),
            models.Index(fields=["region", "district", "is_delete"]),
            models.Index(fields=["filial", "sorting", "is_delete"]),
        ]

    def __str__(self):
        return self.name or f"Warehouse #{self.pk}"


class Currency(BaseModel):
    code = models.CharField(_('Currency code'), max_length=50, null=True, blank=True, help_text=_("Valyuta kodi"))
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Valyuta nomi"))

    class Meta:
        verbose_name = _('Currency')
        verbose_name_plural = _('Currencies')

    def __str__(self):
        return f"{self.name}"


class Note(BaseModel):
    class STATUS(models.TextChoices):
        NEW = 'new', _('New')
        DONE = 'done', _('Done')
        EXPIRED = 'expired', _('Expired')

    sorting = models.IntegerField(_('Sorting'), help_text=_("Sorting"))
    date = models.DateTimeField(_('Date'), null=True, blank=True, help_text=_("Sana"))
    title = models.CharField(_('Title'), max_length=255, null=True, blank=True, help_text=_("Sarlavha"))
    text = models.TextField(_('Address'), null=True, blank=True)
    status = models.CharField(choices=STATUS.choices, default=STATUS.NEW, max_length=30, null=True, blank=True, help_text=_("Holati"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    is_read = models.BooleanField(default=False, help_text=_("Is read?"))

    # reminder flaglar
    notified_1day = models.BooleanField(default=False, help_text=_("1 kunlik eslatma yuborilganmi"))
    notified_1hour = models.BooleanField(default=False, help_text=_("1 soatlik eslatma yuborilganmi"))

    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

        indexes = [
            models.Index(fields=["is_delete", "status"]),
            models.Index(fields=["is_delete", "is_read", "status"]),
            models.Index(fields=["is_delete", "date"]),
            models.Index(fields=["is_delete", "notified_1day", "date"]),
            models.Index(fields=["is_delete", "notified_1hour", "date"]),
        ]
    def __str__(self):
        return self.title or f"Note #{self.pk}"