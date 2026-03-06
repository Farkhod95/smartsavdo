from decimal import Decimal
from django.db import transaction
from django.db.models import F, Sum

from inventory.models import ProductHistory
from suppliers.models import PurchaseInvoice, SupplierAccount


def _d(val) -> Decimal:
    try:
        return Decimal(val or 0)
    except Exception:
        return Decimal("0")


def _calc_paid_total(invoice: PurchaseInvoice) -> Decimal:
    """
    given_summa_total_dollar bo'lsa o'shani oladi,
    aks holda qismlardan yig'adi.
    """
    parts_sum = (
        _d(invoice.given_summa_dollar)
        + _d(invoice.given_summa_naqt)
        + _d(invoice.given_summa_kilik)
        + _d(invoice.given_summa_terminal)
        + _d(invoice.given_summa_transfer)
    )

    total = _d(invoice.given_summa_total_dollar)
    if total <= 0 and parts_sum > 0:
        return parts_sum
    return total


@transaction.atomic
def finalize_purchase_invoice(*, invoice: PurchaseInvoice, updated_by) -> PurchaseInvoice:
    """
    Fakturani yakunlash.

    MUHIM:
    - ProductHistory create paytida stock allaqachon o'zgargan deb qabul qilinadi
    - Shu sabab bu yerda ProductStock yoki Product.count qayta o'zgartirilmaydi
    - Aks holda stock 2 marta yurib ketadi
    """

    # qayta tasdiqlashdan himoya
    if invoice.is_karzinka is False:
        return invoice

    items_qs = (
        ProductHistory.objects
        .select_for_update()
        .filter(purchase_invoice_id=invoice.id)
    )

    agg = items_qs.aggregate(
        total_qty=Sum("count"),
        total_sum=Sum(F("real_price") * F("count")),
    )

    product_count = int(agg.get("total_qty") or 0)
    all_product_summa = _d(agg.get("total_sum") or 0).quantize(Decimal("0.01"))
    paid_total = _calc_paid_total(invoice).quantize(Decimal("0.01"))

    total_debt_old = Decimal("0.00")
    total_debt_new = Decimal("0.00")

    # faqat EXTERNAL bo'lsa supplier hisobi yuradi
    if invoice.type == PurchaseInvoice.TYPE.EXTERNAL and invoice.supplier_id:
        account, _ = SupplierAccount.objects.select_for_update().get_or_create(
            supplier_id=invoice.supplier_id,
            defaults={
                "total_turnover": Decimal("0.00"),
                "filial_debt": Decimal("0.00"),
            },
        )

        total_debt_old = _d(account.filial_debt).quantize(Decimal("0.01"))

        # aylanish
        account.total_turnover = (
            _d(account.total_turnover) + all_product_summa
        ).quantize(Decimal("0.01"))

        # yangi qarz
        total_debt_new = (
            total_debt_old + all_product_summa - paid_total
        ).quantize(Decimal("0.01"))

        account.filial_debt = total_debt_new
        account.save(update_fields=["total_turnover", "filial_debt"])

    # INTERNAL bo'lsa supplier qarzi bo'lmaydi
    else:
        total_debt_old = Decimal("0.00")
        total_debt_new = Decimal("0.00")

    invoice.total_debt_old = total_debt_old
    invoice.total_debt = total_debt_new
    invoice.total_debt_today = total_debt_new
    invoice.product_count = product_count
    invoice.all_product_summa = all_product_summa
    invoice.is_karzinka = False
    invoice.updated_by = updated_by

    update_fields = [
        "total_debt_old",
        "total_debt",
        "total_debt_today",
        "product_count",
        "all_product_summa",
        "is_karzinka",
        "updated_by",
    ]

    if hasattr(invoice, "updated_time"):
        update_fields.append("updated_time")

    invoice.save(update_fields=update_fields)
    return invoice