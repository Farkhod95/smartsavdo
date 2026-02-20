from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from accounts.models import Filial, Sklad
from restapp.models import BaseModel
from suppliers.models import PurchaseInvoice


class Unit(BaseModel):
    code = models.CharField(_('Code'), max_length=50, unique=True, null=True, blank=True, help_text=_('Masalan: "kg", "dona", "karobka", "komplekt", "litr", "pochka", "sm", "m2"'))
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_('Ko‘rinadigan nom: "Kilogramm", "Dona", "Karobka"...'))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))

    class Meta:
        verbose_name = _('unit')
        verbose_name_plural = _('units')

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code and self.name else self.code or self.name or f"Unit #{self.pk}"


# Mahsulot bo'limi: Chinni buyumlar, Elektronika, xoz tavar ...
class ProductBranch(BaseModel):
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Mahsulot bo'limi nomi"))
    sorting = models.IntegerField(null=True, blank=True, help_text=_("Sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('product branch')
        verbose_name_plural = _('product branches')

    def __str__(self):
        return self.name or f"ProductBranch #{self.pk}"

class ProductBranchCategory(BaseModel):
    product_branch = models.ForeignKey(
        ProductBranch,
        related_name='branch_categories',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("ProductBranch bilan bog'lanish")
    )
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Mahsulot bo'limi nomi"))
    sorting = models.IntegerField(null=True, blank=True, help_text=_("Sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('product branch Category')
        verbose_name_plural = _('product branch Categories')

        # ✅ HAR BIR product_branch bo'yicha sorting UNIQUE
        # sorting NULL bo'lsa unique tekshirmasin (NULL ko'p bo'lishi mumkin)
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['product_branch', 'sorting'],
        #         condition=Q(sorting__isnull=False),
        #         name='uq_branchcategory_branch_sorting_notnull'
        #     )
        # ]

    def __str__(self):
        return self.name or f"ProductBranchCategory #{self.pk}"



class ProductModel(BaseModel):
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True,
                            help_text=_("Model nomi (masalan: N-1, Grafin nabor, Termos, Artel, Canon, Samsung)"))
    branch = models.ForeignKey(
        ProductBranch,
        related_name='product_models',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("ProductBranch bilan bog'lanish")
    )
    branch_category = models.ForeignKey(
        ProductBranchCategory,
        related_name='product_models',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Product Branch Category bilan bog'lanish")
    )
    sorting = models.IntegerField(null=True, blank=True, help_text=_("Sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    elegant_id = models.IntegerField(null=True, blank=True, help_text=_("Elegant Id"))

    class Meta:
        verbose_name = _('product model')
        verbose_name_plural = _('product models')

        # ✅ HAR BIR branch_category bo'yicha sorting UNIQUE (NULL bo'lsa tekshirmaydi)
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['branch_category', 'sorting'],
        #         condition=Q(sorting__isnull=False),
        #         name='uq_productmodel_branchcategory_sorting_notnull'
        #     )
        # ]

    def __str__(self):
        return self.name or f"ProductModel #{self.pk}"



class ProductType(BaseModel):
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Turi (masalan: Piyola, Kosa, Tarelka, Printer, Monitor)"))
    branch = models.ForeignKey(
        ProductBranch,
        related_name='product_types',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("ProductBranch bilan bog'lanish")
    )
    branch_category = models.ForeignKey(
        ProductBranchCategory,
        related_name='product_types',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Product Branch Category bilan bog'lanish")
    )
    madel = models.ForeignKey(
        ProductModel,
        related_name='product_types',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("ProductModel bilan bog'lanish")
    )
    sorting = models.IntegerField(null=True, blank=True, help_text=_("Sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    elegant_id = models.IntegerField(null=True, blank=True, help_text=_("Elegant Id"))

    class Meta:
        verbose_name = _('product type')
        verbose_name_plural = _('product types')

        # ✅ HAR BIR madel (ProductModel) bo'yicha sorting UNIQUE (sorting NULL bo'lsa tekshirmaydi)
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['madel', 'sorting'],
        #         condition=Q(sorting__isnull=False),
        #         name='uq_producttype_model_sorting_notnull'
        #     )
        # ]

    def __str__(self):
        return self.name or f"ProductType #{self.pk}"


class ProductTypeSize(BaseModel):
    product_type = models.ForeignKey(ProductType, related_name='product_type_sizes', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductType bilan bog'lanish"))
    size = models.FloatField(_('Size'), null=True, blank=True, help_text=_("O'lcham qiymati (masalan: 12, 64, 1.5 ...)"))
    unit = models.ForeignKey(Unit, related_name='product_type_sizes', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Unit (o'lchov birligi) bilan bog'lanish"))
    sorting = models.IntegerField(null=True, blank=True, help_text=_("Sorting"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    elegant_id = models.IntegerField(null=True, blank=True, help_text=_("Elegant Id"))

    class Meta:
        verbose_name = _('product type size')
        verbose_name_plural = _('product type sizes')

    def __str__(self):
        return f"{self.product_type} | {self.size} {self.unit}" if self.product_type else f"ProductTypeSize #{self.pk}"


class Product(BaseModel):
    date = models.DateField(_('Date'), null=True, blank=True, help_text=_("Kirim sanasi"))
    reserve_limit = models.IntegerField(_('Reserve limit'), null=True, blank=True, help_text=_("Zaxira limiti (nechta qolganda ogohlantirishi)"))
    filial = models.ForeignKey(Filial, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    branch = models.ForeignKey(ProductBranch, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductBranch bilan bog'lanish"))
    branch_category = models.ForeignKey(ProductBranchCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductBranch Category bilan bog'lanish"))
    model = models.ForeignKey(ProductModel, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductModel bilan bog'lanish"))
    type = models.ForeignKey(ProductType, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductType bilan bog'lanish"))
    size = models.ForeignKey(ProductTypeSize, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductTypeSize bilan bog'lanish"))
    count = models.IntegerField(_('Count'), null=True, blank=True, help_text=_("Miqdor"))
    real_price = models.DecimalField(_('Real price'), max_digits=20, decimal_places=2, default=0, help_text=_("Xaqiqiy narxi"))
    unit_price = models.DecimalField(_('Unit price'), max_digits=20, decimal_places=2, default=0, help_text=_("Dona narxi"))
    wholesale_price = models.DecimalField(_('Wholesale price'), max_digits=20, decimal_places=2, default=0, help_text=_("Optom narxi"))
    min_price = models.DecimalField(_('Min price'), max_digits=20, decimal_places=2, default=0, help_text=_("Minimal narxi"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        indexes = [
            models.Index(fields=['is_delete']),
            models.Index(fields=['is_active']),
            models.Index(fields=['date']),
            models.Index(fields=['filial']),
            models.Index(fields=['branch']),
            models.Index(fields=['branch_category']),
            models.Index(fields=['model']),
            models.Index(fields=['type']),
            models.Index(fields=['size']),
        ]

    def __str__(self):
        return f"Product #{self.pk}" if self.pk else "Product"

    def recalc_count_from_stocks(self, save: bool = True):
        total = (
            self.product_stocks
            .filter(product_id=self.pk)
            .aggregate(s=Sum('count'))
            .get('s')
        )
        total = int(total or 0)

        if self.count != total:
            self.count = total
            if save:
                self.save(update_fields=['count'])
        return total


class ProductHistory(BaseModel):
    date = models.DateField(_('Date'), default=timezone.now(), null=True, blank=True, help_text=_("Kirim sanasi"))
    reserve_limit = models.IntegerField(_('Reserve limit'), null=True, blank=True, help_text=_("Zaxira limiti (nechta qolganda ogohlantirishi)"))
    product = models.ForeignKey(Product, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Product bilan bog'lanish"))
    filial = models.ForeignKey(Filial, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True,
                               help_text=_("Filial bilan bog'lanish"))
    sklad = models.ForeignKey(Sklad, related_name='product_histories', on_delete=models.SET_NULL, null=True,
                               blank=True, help_text=_("Filial bilan bog'lanish"))
    purchase_invoice = models.ForeignKey(PurchaseInvoice, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("PurchaseInvoice bilan bog'lanish"))
    branch = models.ForeignKey(ProductBranch, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductBranch bilan bog'lanish"))
    branch_category = models.ForeignKey(ProductBranchCategory, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductBranch Category bilan bog'lanish"))
    model = models.ForeignKey(ProductModel, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductModel bilan bog'lanish"))
    type = models.ForeignKey(ProductType, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductType bilan bog'lanish"))
    size = models.ForeignKey(ProductTypeSize, related_name='product_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductTypeSize bilan bog'lanish"))
    count = models.IntegerField(_('Count'), null=True, blank=True, help_text=_("Miqdor"))
    real_price = models.DecimalField(_('Real price'), max_digits=20, decimal_places=2, default=0, help_text=_("Xaqiqiy narxi"))
    unit_price = models.DecimalField(_('Unit price'), max_digits=20, decimal_places=2, default=0, help_text=_("Dona narxi"))
    wholesale_price = models.DecimalField(_('Wholesale price'), max_digits=20, decimal_places=2, default=0, help_text=_("Optom narxi"))
    min_price = models.DecimalField(_('Min price'), max_digits=20, decimal_places=2, default=0, help_text=_("Minimal narxi"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))

    class Meta:
        verbose_name = _('product history')
        verbose_name_plural = _('product histories')

    def __str__(self):
        return f"ProductHistory #{self.pk}" if self.pk else "ProductHistory"


class ProductStock(BaseModel):
    product = models.ForeignKey(Product, related_name='product_stocks', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Product bilan bog'lanish"))
    sklad = models.ForeignKey(Sklad, related_name='product_stocks', on_delete=models.SET_NULL, null=True, blank=True,
                              help_text=_("Sklad bilan bog'lanish"))
    count = models.IntegerField(_('Count'), null=True, blank=True, help_text=_("Miqdor"))

    class Meta:
        verbose_name = _('Product Stock')
        verbose_name_plural = _('Product Stocks')
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sklad']),
        ]

    def __str__(self):
        return f"Product Stock #{self.pk}" if self.pk else "Product Stock"


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Product bilan bog'lanish"))
    file = models.FileField(upload_to='product-image/%Y/%m/%d', null=True, blank=True, help_text=_("Fayl o‘zi (rasm, pdf, doc va h.k.)"))

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')

    def __str__(self):
        return f"ProductImage #{self.pk}" if self.pk else "ProductImage"
