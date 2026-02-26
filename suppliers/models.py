from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from accounts.models import Filial, Sklad, Region, District
from restapp.models import BaseModel
from django.conf import settings


class Supplier(BaseModel):
    class TYPE(models.TextChoices):
        EXTERNAL = 'external', _('Tashqi')
        INTERNAL = 'internal', _('Ichki')

    type = models.CharField(choices=TYPE.choices, max_length=50, null=True, blank=True, help_text=_("Tip"))
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Ta'minotchi nomi"))
    filial = models.ForeignKey(Filial, related_name='suppliers', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    region = models.ForeignKey(Region, related_name='suppliers', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Viloyat jadvali bilan bog'lanish"))
    district = models.ForeignKey(District, related_name='suppliers', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Tuman jadvali bilan bog'lanish"))
    address = models.TextField(_('Address'), null=True, blank=True, help_text=_("Manzil"))
    inn = models.IntegerField(_('INN'), null=True, blank=True, help_text=_("INN"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')

    def __str__(self):
        return self.name or f"Supplier #{self.pk}"


class SupplierAccount(BaseModel):
    supplier = models.ForeignKey(Supplier, related_name='supplier_accounts', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Supplier bilan bog'lanish"))
    total_turnover = models.DecimalField(_('Total turnover'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy tavarlar aylanmasi"))
    filial_debt = models.DecimalField(_('Filial debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Taminotchidan qarz"))

    class Meta:
        verbose_name = _('supplier account')
        verbose_name_plural = _('supplier accounts')

    def __str__(self):
        return f"{self.supplier} | Account #{self.pk}" if self.supplier else f"SupplierAccount #{self.pk}"


class SupplierDebtRepayment(BaseModel):
    supplier = models.ForeignKey(Supplier, related_name='debt_repayments', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Supplier bilan bog'lanish"))
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='supplier_debt_repayments', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Xodim (User)"))
    date = models.DateField(_('Date'), default=timezone.localdate, null=True, blank=True, help_text=_("To'lov sanasi"))
    total_debt_old = models.DecimalField(_('Old debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Eski qarz"))
    total_debt = models.DecimalField(_('Total debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Qolgan qarz"))
    summa_total_dollar = models.DecimalField(_('Total paid (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy to'langan qarz dollarda"))
    summa_dollar = models.DecimalField(_('Paid dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan qarz dollarda"))
    summa_naqt = models.DecimalField(_('Paid cash'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan qarz naqtda"))
    summa_kilik = models.DecimalField(_('Paid click/debt'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan qarz kilikda"))
    summa_terminal = models.DecimalField(_('Paid terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan qarz terminalda"))
    summa_transfer = models.DecimalField(_('Paid transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan qarz transferda"))

    class Meta:
        verbose_name = _('supplier debt repayment')
        verbose_name_plural = _('supplier debt repayments')

    def __str__(self):
        return f"SupplierDebtRepayment #{self.pk}" if self.pk else "SupplierDebtRepayment"


class PurchaseInvoice(BaseModel):
    class TYPE(models.TextChoices):
        EXTERNAL = 'external', _('Tashqi kirim')
        INTERNAL = 'internal', _('Ichki kirim')

    type = models.CharField(choices=TYPE.choices, max_length=50, null=True, blank=True, help_text=_("Tip"))
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='purchase_invoices', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Xodim (User)"))
    supplier = models.ForeignKey(Supplier, related_name='purchase_invoices', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Supplier bilan bog'lanish"))
    sklad_outgoing = models.ForeignKey(Sklad, related_name='purchase_sklad_outgoing', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Yuk Chiquvchi Sklad bilan bog'lanish"))
    filial = models.ForeignKey(Filial, related_name='purchase_invoices', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    sklad = models.ForeignKey(Sklad, related_name='purchase_invoices', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Yuk kiruvchi Sklad bilan bog'lanish"))
    date = models.DateField(_('Date'), default=timezone.localdate, null=True, blank=True, help_text=_("Faktura sanasi"))
    total_debt_old = models.DecimalField(_('Old debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Eski qarz"))
    total_debt = models.DecimalField(_('Total debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Qolgan qarz"))
    total_debt_today = models.DecimalField(_('Today debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Bugungi qolgan qarz"))
    product_count = models.IntegerField(_('Product count'), null=True, blank=True, help_text=_("Mahsulotlar soni"))
    all_product_summa = models.DecimalField(_('All product summa'), max_digits=20, decimal_places=2, default=0, help_text=_("Barcha mahsulot summasi"))
    given_summa_total_dollar = models.DecimalField(_('Given total (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy berilgan summa dollarda"))
    given_summa_dollar = models.DecimalField(_('Given dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("Berilgan summa dollarda"))
    given_summa_naqt = models.DecimalField(_('Given cash'), max_digits=20, decimal_places=2, default=0, help_text=_("Berilgan summa naqtda"))
    given_summa_kilik = models.DecimalField(_('Given click/debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Berilgan summa kilikda"))
    given_summa_terminal = models.DecimalField(_('Given terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("Berilgan summa terminalda"))
    given_summa_transfer = models.DecimalField(_('Given transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("Berilgan summa transferda"))
    is_karzinka = models.BooleanField(default=True, help_text=_("Karzinkaga qoshilganmi?"))

    class Meta:
        verbose_name = _('purchase invoice')
        verbose_name_plural = _('purchase invoices')

    def __str__(self):
        return f"PurchaseInvoice #{self.pk}" if self.pk else "PurchaseInvoice"