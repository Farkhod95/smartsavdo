from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from accounts.models import Region, District, Filial, Sklad, Currency
from inventory.models import ProductBranch, ProductModel, ProductType, ProductTypeSize, Product, ProductBranchCategory
from restapp.models import BaseModel
from django.conf import settings


class Client(BaseModel):
    telegram_id = models.BigIntegerField(_('Telegram ID'), null=True, blank=True, help_text=_("Telegram ID"))
    full_name = models.CharField(_('Full name'), max_length=255, null=True, blank=True, help_text=_("F.I.Sh"))
    is_active = models.BooleanField(default=True, help_text=_("Is active?"))
    date_of_birthday = models.DateField(_('Date of birthday'), null=True, blank=True, help_text=_("Tug'ilgan sana"))
    gender = models.CharField(_('Gender'), max_length=50, null=True, blank=True, help_text=_("Jinsi"))
    phone_number = models.CharField(_('Phone number'), max_length=64, null=True, blank=True, help_text=_("Telefon raqam"))
    region = models.ForeignKey(Region, related_name='clients', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Viloyat"))
    district = models.ForeignKey(District, related_name='clients', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Tuman"))
    filial = models.ForeignKey(Filial, related_name='clients', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial"))
    total_debt = models.DecimalField(_('Total debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy qarz"))
    keshbek = models.DecimalField(_('Cashback percent'), max_digits=10, decimal_places=2, default=0, help_text=_("Keshbek foizda (0.2, 0.5 ...)"))
    is_profit_loss = models.BooleanField(default=False, help_text=_("Foyda/zararni hisoblamaslik uchun"))
    type = models.IntegerField(_('Type'), null=True, blank=True, help_text=_("Dona, Optom, Dokon, Hamkor"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('client')
        verbose_name_plural = _('clients')

    def __str__(self):
        return self.full_name or f"Client #{self.pk}"


class ClientKeshbekHistory(BaseModel):
    client = models.ForeignKey(Client, related_name='keshbek_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Client bilan bog'lanish"))
    keshbek = models.DecimalField(_('Cashback percent'), max_digits=10, decimal_places=2, default=0, help_text=_("Foizda (0.2, 0.5 ...)"))
    keshbek_summa = models.DecimalField(_('Cashback summa'), max_digits=20, decimal_places=2, default=0, help_text=_("Keshbek summasi"))
    order_history = models.IntegerField(_('Order history'), null=True, blank=True, help_text=_("OrderHistory jadvali ID (int)"))

    class Meta:
        verbose_name = _('client cashback history')
        verbose_name_plural = _('client cashback histories')

    def __str__(self):
        return f"ClientKeshbekHistory #{self.pk}" if self.pk else "ClientKeshbekHistory"


class Order(BaseModel):
    number_of_order = models.IntegerField(_('Number of order'), null=True, blank=True, help_text=_("Buyurtma raqami"))
    client = models.ForeignKey(Client, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Client bilan bog'lanish"))
    filial = models.ForeignKey(Filial, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    date_last_order = models.DateField(_('Date last order'), null=True, blank=True, help_text=_("Oxirgi buyurtma sanasi"))
    all_profit_dollar = models.DecimalField(_('All profit (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy foyda (dollarda)"))
    total_debt_client = models.DecimalField(_('Total client debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijozning umumiy qarzi"))
    total_debt_old_client = models.DecimalField(_('Old client debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijozning eski qarzi"))
    all_product_summa = models.DecimalField(_('All product summa'), max_digits=20, decimal_places=2, default=0, help_text=_("Barcha mahsulot summasi"))
    summa_total_dollar = models.DecimalField(_('Total paid (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy to'langan summa dollarda"))
    summa_dollar = models.DecimalField(_('Paid dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa dollarda"))
    summa_naqt = models.DecimalField(_('Paid cash'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa naqtda"))
    summa_kilik = models.DecimalField(_('Paid click/debt'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa kilikda"))
    summa_terminal = models.DecimalField(_('Paid terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa terminalda"))
    summa_transfer = models.DecimalField(_('Paid transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("To'langan summa transferda"))
    discount_amount = models.DecimalField(_('Discount amount'), max_digits=20, decimal_places=2, default=0, help_text=_("Chegirma"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')

    def __str__(self):
        return f"Order #{self.pk}" if self.pk else "Order"


class OrderHistory(BaseModel):
    order = models.ForeignKey(Order, related_name='order_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Order bilan bog'lanish"))
    client = models.ForeignKey(Client, related_name='order_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Client bilan bog'lanish"))
    order_filial = models.ForeignKey(Filial, related_name='order_histories', on_delete=models.SET_NULL, null=True, blank=True,
                               help_text=_("Filial bilan bog'lanish"))
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='order_histories', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Buyurtmani qabul qilgan hodim (User)"))
    currency = models.ForeignKey(Currency, related_name='order_histories', on_delete=models.SET_NULL, null=True,
                                 blank=True, help_text=_("Valyuta bilan bog'lanish"))
    exchange_rate = models.DecimalField(_('Exchange rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Kurs"))
    date = models.DateField(_('Date'), default=timezone.localdate, null=True, blank=True, help_text=_("Sana"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))
    all_profit_dollar = models.DecimalField(_('All profit (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Shu buyurtmadagi foyda"))
    total_debt_client = models.DecimalField(_('Total client debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijoz qarzi"))
    total_debt_today_client = models.DecimalField(_('Today client debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Shu buyurtmadagi mijoz qarzi"))
    all_product_summa = models.DecimalField(_('All product summa'), max_digits=20, decimal_places=2, default=0, help_text=_("Barcha mahsulotlar narxi"))
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
    order_status = models.BooleanField(default=False, help_text=_("Buyurtma tasdiqlanganmi? (Narxini kiritishda)"))
    update_status = models.IntegerField(_('Update status'), null=True, blank=True, help_text=_("Buyurtma o'zgarganmi?"))
    is_debtor_product = models.BooleanField(default=False, help_text=_("Mijozdan qarzdorlik mavjudmi? (Hamma mahsuloti berildimi?)"))
    status_order_dukon = models.BooleanField(default=False, help_text=_("Do'konda buyurtma xolati"))
    status_order_sklad = models.BooleanField(default=False, help_text=_("Skladda buyurtma xolati"))
    driver_info = models.CharField(_('Driver info'), max_length=255, null=True, blank=True, help_text=_("Haydovchi ma'lumotlari"))
    is_karzinka = models.BooleanField(default=True, help_text=_("Karzinkaga qoshilganmi?"))

    class Meta:
        verbose_name = _('order history')
        verbose_name_plural = _('order histories')

        indexes = [
            models.Index(fields=['created_by', 'is_delete', 'date']),
            models.Index(fields=['created_by', 'is_delete', 'created_time']),
        ]

    def __str__(self):
        return f"OrderHistory #{self.pk}" if self.pk else "OrderHistory"


class VozvratOrder(BaseModel):
    filial = models.ForeignKey(Filial, related_name='vozvrat_orders', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Filial bilan bog'lanish"))
    client = models.ForeignKey(Client, related_name='vozvrat_orders', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Client bilan bog'lanish"))
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vozvrat_orders', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Jarayonni amalga oshirgan hodim (User)"))
    exchange_rate = models.DecimalField(_('Exchange rate'), max_digits=20, decimal_places=6, default=0, help_text=_("Kurs"))
    date = models.DateField(_('Date'), default=timezone.localdate, null=True, blank=True, help_text=_("Sana"))
    note = models.TextField(_('Note'), null=True, blank=True, help_text=_("Izoh"))
    old_total_debt_client = models.DecimalField(_('Old total debt client'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijozning eski qarzi"))
    total_debt_client = models.DecimalField(_('Total debt client'), max_digits=20, decimal_places=2, default=0, help_text=_("Mijoz qarzi"))
    summa_total_dollar = models.DecimalField(_('Total refunded (USD)'), max_digits=20, decimal_places=2, default=0, help_text=_("Umumiy qaytarilgan summa dollarda"))
    summa_dollar = models.DecimalField(_('Refunded dollar'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytarilgan summa dollarda"))
    summa_naqt = models.DecimalField(_('Refunded cash'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytarilgan summa naqtda"))
    summa_kilik = models.DecimalField(_('Refunded click/debt'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytarilgan summa kilikda"))
    summa_terminal = models.DecimalField(_('Refunded terminal'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytarilgan summa terminalda"))
    summa_transfer = models.DecimalField(_('Refunded transfer'), max_digits=20, decimal_places=2, default=0, help_text=_("Qaytarilgan summa transferda"))
    discount_amount = models.DecimalField(_('Discount amount'), max_digits=20, decimal_places=2, default=0, help_text=_("Chegirma"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    is_vazvrat_status = models.BooleanField(default=False, help_text=_("Tasdiqlandimi?"))
    is_karzinka = models.BooleanField(default=True, help_text=_("Karzinkaga qoshilganmi?"))

    class Meta:
        verbose_name = _('vozvrat order')
        verbose_name_plural = _('vozvrat orders')

    def __str__(self):
        return f"VozvratOrder #{self.pk}" if self.pk else "VozvratOrder"


class OrderHistoryProduct(BaseModel):
    date = models.DateField(_('Date'), null=True, blank=True, help_text=_("Sana"))
    order_history = models.ForeignKey(OrderHistory, related_name='products_order_history', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("OrderHistory bilan bog'lanish"))
    product = models.ForeignKey(Product, related_name='Order_products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Mahsulot bilan bog'lanish"))
    vozvrat_order = models.ForeignKey(VozvratOrder, related_name='order_history_products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("VozvratOrder bilan bog'lanish"))
    sklad = models.ForeignKey(Sklad, related_name='Order_products', on_delete=models.SET_NULL, null=True, blank=True,
                               help_text=_("Filial bilan bog'lanish"))
    branch = models.ForeignKey(ProductBranch, related_name='order_history_products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductBranch bilan bog'lanish"))
    branch_category = models.ForeignKey(ProductBranchCategory, related_name='order_history_products',
                                        on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductBranch Category bilan bog'lanish"))
    model = models.ForeignKey(ProductModel, related_name='order_history_products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductModel bilan bog'lanish"))
    type = models.ForeignKey(ProductType, related_name='order_history_products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductType bilan bog'lanish"))
    size = models.ForeignKey(ProductTypeSize, related_name='order_history_products', on_delete=models.SET_NULL, null=True, blank=True, help_text=_("ProductTypeSize bilan bog'lanish"))
    count = models.IntegerField(_('Count'), null=True, blank=True, help_text=_("Miqdor"))
    price_dollar = models.DecimalField(_('Price dollar'), max_digits=20, decimal_places=2, default=0,
                                       help_text=_("Narxi dollarda"))
    price_sum = models.DecimalField(_('Price sum'), max_digits=20, decimal_places=2, default=0,
                                    help_text=_("Narxi so'mda"))
    given_count = models.IntegerField(_('Given count'), null=True, blank=True, help_text=_("Mijozga berilgan mahsulot soni"))
    real_price = models.DecimalField(_('Real price'), max_digits=20, decimal_places=2, default=0, help_text=_("Xaqiqiy narxi"))
    unit_price = models.DecimalField(_('Unit price'), max_digits=20, decimal_places=2, default=0, help_text=_("Dona narxi"))
    wholesale_price = models.DecimalField(_('Wholesale price'), max_digits=20, decimal_places=2, default=0, help_text=_("Optom narxi"))
    is_delete = models.BooleanField(default=False, help_text=_("Is deleted?"))
    cargo_terminal = models.CharField(_('Cargo terminal'), max_length=255, null=True, blank=True, help_text=_("Do'kon yoki Sklad (Yuk chiqish joyi)"))
    price_difference = models.BooleanField(default=False, help_text=_("Narxda farq bormi? (Sotilgan narx real dan kichikmi)"))
    status_order = models.BooleanField(default=False, help_text=_("Tovar xolati (tayyormi?)"))
    is_karzinka = models.BooleanField(default=False, help_text=_("Karzinkaga qoshilganmi?"))

    class Meta:
        verbose_name = _('order history product')
        verbose_name_plural = _('order history products')

    def __str__(self):
        return f"OrderHistoryProduct #{self.pk}" if self.pk else "OrderHistoryProduct"