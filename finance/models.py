from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import Filial
from restapp.models import BaseModel
from django.conf import settings

from sales.models import Client


class ExchangeRate(BaseModel):
    dollar = models.DecimalField(_('Dollar rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Dollar kursi"))
    filial = models.ForeignKey(Filial, related_name='exchange_rates', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))

    class Meta:
        verbose_name = _('exchange rate')
        verbose_name_plural = _('exchange rates')

    def __str__(self):
        return f"{self.filial} | {self.dollar}" if self.filial else f"ExchangeRate #{self.pk}"


class ExchangeRateHistory(BaseModel):
    exchange_rate = models.ForeignKey(ExchangeRate, related_name='exchange_rate_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Dollar kursi bilan bog'lanish"))
    old_dollar = models.DecimalField(_('Dollar rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Eski Dollar kursi"))
    new_dollar = models.DecimalField(_('Dollar rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Yangi Dollar kursi"))
    filial = models.ForeignKey(Filial, related_name='exchange_rate_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))

    class Meta:
        verbose_name = _('Exchange rate history')
        verbose_name_plural = _('Exchange rate histories')

    def __str__(self):
        return f"{self.filial} | {self.new_dollar}" if self.filial else f"ExchangeRateHistory #{self.pk}"


class ExpenseCategory(BaseModel):
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True, help_text=_("Xarajat kategoriyasi nomi"))

    class Meta:
        verbose_name = _('expense category')
        verbose_name_plural = _('expense categories')

    def __str__(self):
        return self.name or f"ExpenseCategory #{self.pk}"


class Expense(BaseModel):
    filial = models.ForeignKey(Filial, related_name='expenses', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    exchange_rate = models.DecimalField(_('Exchange rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Kurs"))
    category = models.ForeignKey(ExpenseCategory, related_name='expenses', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ExpenseCategory bilan bog'lanish"))
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='expenses', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Jarayonni amalga oshirgan hodim (User)"))
    is_salary = models.BooleanField(default=False, help_text=_("is salary?"))
    summa_total_dollar = models.DecimalField(_('Total (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Xarajatlar summa dollar ko'rinishida"))
    summa_dollar = models.DecimalField(_('Dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("Xarajatlar summa dollarda"))
    summa_naqt = models.DecimalField(_('Cash'), max_digits=20, decimal_places=2, default=0, help_text=_("Xarajatlar summa naqtda"))
    summa_kilik = models.DecimalField(_('Click'), max_digits=20, decimal_places=2, default=0, help_text=_("Xarajatlar summa kilikda"))
    summa_terminal = models.DecimalField(_('Terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("Xarajatlar summa terminalda"))
    summa_transfer = models.DecimalField(_('Transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("Xarajatlar summa transferda"))
    date = models.DateField(_('Date'), null=True, blank=True, help_text=_("Sana"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('expense')
        verbose_name_plural = _('expenses')

    def __str__(self):
        return f"Expense #{self.pk}" if self.pk else "Expense"


class DebtRepayment(BaseModel):
    filial = models.ForeignKey(Filial, related_name='debt_repayments', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    client = models.ForeignKey(Client, related_name='debt_repayments', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Client bilan bog'lanish"))
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='debt_repayments', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Jarayonni amalga oshirgan hodim (User)"))
    exchange_rate = models.DecimalField(_('Exchange rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Kurs"))
    date = models.DateField(_('Date'), null=True, blank=True, help_text=_("Sana"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))
    old_total_debt_client = models.DecimalField(_('Old total debt client'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijozning eski qarzi"))
    total_debt_client = models.DecimalField(_('Total debt client'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijoz qarzi"))
    summa_total_dollar = models.DecimalField(_('Total paid (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy to'langan summa dollarda"))
    summa_dollar = models.DecimalField(_('Paid dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa dollarda"))
    summa_naqt = models.DecimalField(_('Paid cash'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa naqtda"))
    summa_kilik = models.DecimalField(_('Paid click/debt'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa kilikda"))
    summa_terminal = models.DecimalField(_('Paid terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa terminalda"))
    summa_transfer = models.DecimalField(_('Paid transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa transferda"))
    discount_amount = models.DecimalField(_('Discount amount'), max_digits=20, decimal_places=2, default=0, help_text=_("Chegirma"))
    zdacha_dollar = models.DecimalField(_('Change (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytim dollarda"))
    zdacha_som = models.DecimalField(_('Change (UZS)'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytim so'mda"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    debt_status = models.BooleanField(default=False, help_text=_("To'langan qarz tasdiqlanganmi?"))

    class Meta:
        verbose_name = _('debt repayment')
        verbose_name_plural = _('debt repayments')

    def __str__(self):
        return f"DebtRepayment #{self.pk}" if self.pk else "DebtRepayment"
