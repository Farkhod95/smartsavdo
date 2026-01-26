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
        return f"{self.code}"


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


class ProductCategory(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True, help_text=_("Nomi"))
    sorting = models.IntegerField(null=True, blank=True, unique=True, help_text=_("sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')

    def __str__(self):
        return f"{self.name}"


class Model(BaseModel):
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Nomi"))
    category = models.ForeignKey(ProductCategory, related_name='model_category', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Kategoriya"))
    sorting = models.IntegerField(null=True, blank=True, unique=True, help_text=_("sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Model')
        verbose_name_plural = _('Modeles')

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class ModelType(BaseModel):
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Nomi"))
    model = models.ForeignKey(Model, related_name='model_type_model', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Model"))
    sorting = models.IntegerField(null=True, blank=True, unique=True, help_text=_("sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Model Type')
        verbose_name_plural = _('Model Types')

    def __str__(self):
        return f"{self.model.name} / {self.name}"


class ModelSize(BaseModel):
    class TYPE(models.TextChoices):
        TYPE_1 = '1', _('Dona')
        TYPE_2 = '2', _('Karobka')
        TYPE_3 = '3', _('Komplekt')
        TYPE_4 = '4', _('Pochka')


    model_type = models.ForeignKey(ModelType, related_name='model_size_model_type', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Model Type"))
    size = models.FloatField(_('Size'), null=True, blank=True, help_text=_("Size"))
    type = models.CharField(max_length=30, choices=TYPE.choices, null=True, blank=True, verbose_name=_('Holati'),
                              help_text=_("Turi"))
    sorting = models.IntegerField(null=True, blank=True, unique=True, help_text=_("sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Model Size')
        verbose_name_plural = _('Model Sizes')

    def __str__(self):
        return self.id
