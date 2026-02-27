from decimal import Decimal
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from inventory.models import ProductHistory, Product, ProductStock
from suppliers.models import (
    PurchaseInvoice,
    SupplierAccount,
    SupplierDebtRepayment,
)


def _d(val) -> Decimal:
    try:
        return Decimal(val or 0)
    except Exception:
        return Decimal('0')


def _calc_paid_total(invoice: PurchaseInvoice) -> Decimal:
    """
    Sizda allaqachon given_summa_total_dollar bor.
    Lekin xavfsiz bo'lishi uchun komponentlardan ham yig'amiz.
    """
    parts_sum = (
        _d(invoice.given_summa_dollar)
        + _d(invoice.given_summa_naqt)
        + _d(invoice.given_summa_kilik)
        + _d(invoice.given_summa_terminal)
        + _d(invoice.given_summa_transfer)
    )

    # agar total field to‘g‘ri yuritilsa – o‘shani ishlatamiz,
    # aks holda komponentlar yig‘indisini.
    total = _d(invoice.given_summa_total_dollar)
    if total <= 0 and parts_sum > 0:
        return parts_sum
    return total


def _get_or_create_product_from_history(ph: ProductHistory) -> Product:
    """
    ProductHistory satridan Product topish / yaratish.
    Product unique constraint yo‘q, shuning uchun “kalit” sifatida
    filial+branch+branch_category+model+type+size ni ishlatyapmiz.
    """
    product, _created = Product.objects.get_or_create(
        filial_id=ph.filial_id,
        branch_id=ph.branch_id,
        branch_category_id=ph.branch_category_id,
        model_id=ph.model_id,
        type_id=ph.type_id,
        size_id=ph.size_id,
        defaults={
            "date": ph.date or timezone.localdate(),
            "reserve_limit": ph.reserve_limit,
            "real_price": ph.real_price or 0,
            "unit_price": ph.unit_price or 0,
            "wholesale_price": ph.wholesale_price or 0,
            "min_price": ph.min_price or 0,
            "note": ph.note,
            "is_delete": False,
            "is_active": True,
            "count": 0,
        }
    )
    return product


@transaction.atomic
def finalize_purchase_invoice(*, invoice: PurchaseInvoice, updated_by) -> PurchaseInvoice:
    """
    PurchaseInvoice DONE (yakunlash) – to‘liq hisob-kitob.

    QAYERDAN ITEM OLADI?
    - Sizdagi modelga qarab eng mantiqli joy: ProductHistory(purchase_invoice=invoice)
      (kirim “karzinka” qilib shu yerga yozib borilgan deb qabul qilyapman)
    """

    # 0) qayta DONE bo'lishdan himoya (xohlasangiz)
    if invoice.is_karzinka is False:
        return invoice

    # 1) invoice itemlar
    items_qs = (
        ProductHistory.objects
        .select_for_update()
        .filter(purchase_invoice_id=invoice.id)
    )

    # 2) product_count va all_product_summa hisoblash
    # Eslatma:
    # - real_price sizda “xaqiqiy narxi” – ko‘pincha dona tannarx bo‘ladi.
    #   Shuning uchun SUM(real_price * count) qilyapmiz.
    # - agar real_price allaqachon “row total” bo‘lsa, unda faqat SUM(real_price) qiling.
    agg = items_qs.aggregate(
        total_qty=Sum('count'),
        total_sum=Sum(F('real_price') * F('count')),
    )
    product_count = int(agg.get('total_qty') or 0)
    all_product_summa = _d(agg.get('total_sum') or 0).quantize(Decimal("0.01"))

    # 3) sklad stock update
    # EXTERNAL: kiruvchi skladga qo‘shiladi
    # INTERNAL: outgoing sklad’dan ayiriladi, kiruvchi skladga qo‘shiladi
    for ph in items_qs:
        qty = int(ph.count or 0)
        if qty == 0:
            continue

        # history’dagi filial/sklad bo‘sh bo‘lsa invoice’dan to‘ldiramiz
        if not ph.filial_id:
            ph.filial_id = invoice.filial_id
        if not ph.sklad_id:
            ph.sklad_id = invoice.sklad_id
        if not ph.date:
            ph.date = invoice.date or timezone.localdate()

        product = ph.product if ph.product_id else _get_or_create_product_from_history(ph)
        if not ph.product_id:
            ph.product = product

        # kiruvchi skladga qo‘shish
        ps_in, _ = ProductStock.objects.get_or_create(
            product_id=product.id,
            sklad_id=invoice.sklad_id,
            defaults={"count": 0},
        )
        ps_in.count = int(ps_in.count or 0) + qty
        ps_in.save(update_fields=["count"])

        # INTERNAL bo'lsa outgoing sklad’dan ayirish
        if invoice.type == PurchaseInvoice.TYPE.INTERNAL and invoice.sklad_outgoing_id:
            ps_out, _ = ProductStock.objects.get_or_create(
                product_id=product.id,
                sklad_id=invoice.sklad_outgoing_id,
                defaults={"count": 0},
            )
            ps_out.count = int(ps_out.count or 0) - qty
            ps_out.save(update_fields=["count"])

        # product total count’ni qayta hisoblash
        product.recalc_count_from_stocks(save=True)

        ph.save(update_fields=["product", "filial", "sklad", "date"])

    # 4) Supplier debt hisoblash (faqat EXTERNAL)
    paid_total = _calc_paid_total(invoice).quantize(Decimal("0.01"))

    total_debt_old = Decimal('0.00')
    total_debt_new = Decimal('0.00')

    if invoice.type == PurchaseInvoice.TYPE.EXTERNAL and invoice.supplier_id:
        account, _ = SupplierAccount.objects.select_for_update().get_or_create(
            supplier_id=invoice.supplier_id,
            defaults={"total_turnover": 0, "filial_debt": 0},
        )

        total_debt_old = _d(account.filial_debt).quantize(Decimal("0.01"))

        # Aylanma: kirim summasi qo‘shiladi
        account.total_turnover = (_d(account.total_turnover) + all_product_summa).quantize(Decimal("0.01"))

        # Debt: eski qarz + bugungi kirim - bugungi to‘lov
        total_debt_new = (total_debt_old + all_product_summa - paid_total).quantize(Decimal("0.01"))

        # xohlasangiz qarzni 0 dan past tushirmang:
        # total_debt_new = max(total_debt_new, Decimal("0.00"))

        account.filial_debt = total_debt_new
        account.save(update_fields=["total_turnover", "filial_debt"])

        # repayment yozuvi (to‘lov bo‘lsa)
        if paid_total > 0:
            SupplierDebtRepayment.objects.create(
                supplier_id=invoice.supplier_id,
                employee=invoice.employee,
                date=invoice.date or timezone.localdate(),

                total_debt_old=total_debt_old,
                total_debt=total_debt_new,

                summa_total_dollar=paid_total,
                summa_dollar=_d(invoice.given_summa_dollar),
                summa_naqt=_d(invoice.given_summa_naqt),
                summa_kilik=_d(invoice.given_summa_kilik),
                summa_terminal=_d(invoice.given_summa_terminal),
                summa_transfer=_d(invoice.given_summa_transfer),
            )

    # 5) invoice’ni final qiymatlar bilan saqlash
    invoice.total_debt_old = total_debt_old
    invoice.total_debt = total_debt_new
    invoice.total_debt_today = total_debt_new

    invoice.product_count = product_count
    invoice.all_product_summa = all_product_summa

    # karzinka yopiladi
    invoice.is_karzinka = False

    # BaseModel’da updated_by bo'lsa:
    invoice.updated_by = updated_by

    invoice.save(update_fields=[
        "total_debt_old", "total_debt", "total_debt_today",
        "product_count", "all_product_summa",
        "is_karzinka",
        "updated_by",
        "updated_time" if hasattr(invoice, "updated_time") else "id",
    ])

    return invoice