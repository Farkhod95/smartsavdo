from django.db import models
from django.utils.translation import gettext_lazy as _

from directory.models import Region, District, Country, ProductCategory, Model, ModelType, ModelSize
from restapp.models import BaseModel



class Product(BaseModel):
    class TYPE(models.TextChoices):
        TYPE_1 = '1', _('Dona')
        TYPE_2 = '2', _('Karobka')
        TYPE_3 = '3', _('Komplekt')
        TYPE_4 = '4', _('Pochka')

    category = models.ForeignKey(ProductCategory, related_name='product_category', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Kategoriya"))
    model = models.ForeignKey(Model, related_name='product_model', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Model"))
    model_type = models.ForeignKey(ModelType, related_name='product_model_type', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Model Type"))
    model_size = models.ForeignKey(ModelSize, related_name='product_model_size', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Model Size"))
    size = models.FloatField(_('Size'), null=True, blank=True, help_text=_("Size"))
    type = models.CharField(max_length=30, choices=TYPE.choices, null=True, blank=True, verbose_name=_('Holati'),
                              help_text=_("Turi"))
    count = models.IntegerField(null=True, blank=True, help_text=_("Count"))
    real_price = models.FloatField(null=True, blank=True, help_text=_("Real Price"))
    price = models.FloatField(null=True, blank=True, help_text=_("Price"))
    sorting = models.IntegerField(null=True, blank=True, unique=True, help_text=_("sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('Task Comment')
        verbose_name_plural = _('Task Comments')
        ordering = ['created_time']

    def __str__(self):
        return f"Product#{self.id}"


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, related_name='attachments', on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='product_image/%Y/%m/%d/', null=True, blank=True, help_text=_("Fayl"))

    class Meta:
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')

    def __str__(self):
        return f"ProductImage#{self.pk}"


class FAQ(BaseModel):

    """Tez-tez so‘raladigan savollar: Contact sahifasi ostida ko‘rsatiladi."""
    question = models.CharField(_('Savol'), max_length=255, null=True, blank=True, help_text=_('Ko‘p so‘raladigan savol matni'))  # Savol
    answer = models.TextField(_('Javob'), null=True, blank=True, help_text=_('Savolga javob matni'))  # Javob matni
    order_index = models.PositiveIntegerField(unique=True, verbose_name=_('Tartib'), help_text=_('Chop etish tartibi'))  # Sortlash

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQ')

    def __str__(self):
        return self.question