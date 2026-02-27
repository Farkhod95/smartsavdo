from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import F, Sum

from inventory.models import ProductHistory, ProductStock
from suppliers.models import (
    PurchaseInvoice,
    SupplierAccount
)


def _d(val) -> Decimal:
    try:
        return Decimal(val or 0)
    except Exception:
        return Decimal("0")


def _calc_paid_total(invoice: PurchaseInvoice) -> Decimal:
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
def delete_purchase_invoice_rollback(*, invoice_id: int, user) -> dict:
    """
    PurchaseInvoice delete:
    - ProductStock rollback (kirimni qaytaradi)
    - SupplierAccount rollback (EXTERNAL bo'lsa)
    - SupplierDebtRepayment ga tegmaydi (siz aytgan talab)
    - ProductHistory(purchase_invoice=...) itemlarni o'chiradi
    - Invoice ni o'chiradi

    NOTE: Bu function "hard delete" qiladi.
    """

    # Invoice ni lock qilib olamiz
    invoice = (
        PurchaseInvoice.objects
        .select_for_update()
        .get(pk=invoice_id)
    )

    # Itemlar (invoice ichidagi mahsulotlar)
    items_qs = (
        ProductHistory.objects
        .select_for_update()
        .filter(purchase_invoice_id=invoice.id)
        .select_related("product")
    )

    # all_product_summa ni itemlardan aniq hisoblab olamiz
    agg = items_qs.aggregate(
        total_qty=Sum("count"),
        total_sum=Sum(F("real_price") * F("count")),
    )
    all_product_summa = _d(agg.get("total_sum") or 0).quantize(Decimal("0.01"))
    paid_total = _calc_paid_total(invoice).quantize(Decimal("0.01"))

    # 1) STOCK rollback
    # - INCOMING sklad: minus qty
    # - INTERNAL bo'lsa: OUTGOING sklad: plus qty (chunki oldin minus qilingandi)
    incoming_sklad_id = invoice.sklad_id
    outgoing_sklad_id = invoice.sklad_outgoing_id if invoice.type == PurchaseInvoice.TYPE.INTERNAL else None

    rolled_back_rows = 0

    for ph in items_qs:
        qty = int(ph.count or 0)
        if qty == 0:
            continue

        product_id = ph.product_id
        if not product_id:
            # Agar history’da product bo'lmasa, rollback qila olmaymiz
            # (normalda bo'lishi kerak)
            continue

        # Incoming sklad'dan ayiramiz
        if incoming_sklad_id:
            ps_in = (
                ProductStock.objects
                .select_for_update()
                .filter(product_id=product_id, sklad_id=incoming_sklad_id)
                .first()
            )
            if ps_in:
                ps_in.count = int(ps_in.count or 0) - qty
                ps_in.save(update_fields=["count"])
                rolled_back_rows += 1

        # INTERNAL bo'lsa outgoing sklad'ga qaytaramiz
        if outgoing_sklad_id:
            ps_out = (
                ProductStock.objects
                .select_for_update()
                .filter(product_id=product_id, sklad_id=outgoing_sklad_id)
                .first()
            )
            if ps_out:
                ps_out.count = int(ps_out.count or 0) + qty
                ps_out.save(update_fields=["count"])
                rolled_back_rows += 1

        # Product total countni qayta hisoblash (sizda method bor)
        if ph.product_id and hasattr(ph.product, "recalc_count_from_stocks"):
            ph.product.recalc_count_from_stocks(save=True)

    # 2) SupplierAccount rollback (faqat EXTERNAL)
    # Invoice ta'siri: debt += all_product_summa - paid_total
    # Delete bo'lsa: debt -= (all_product_summa - paid_total)
    # turnover -= all_product_summa
    supplier_account_updated = False
    if invoice.type == PurchaseInvoice.TYPE.EXTERNAL and invoice.supplier_id:
        account = (
            SupplierAccount.objects
            .select_for_update()
            .filter(supplier_id=invoice.supplier_id)
            .first()
        )
        if account:
            delta_debt = (all_product_summa - paid_total).quantize(Decimal("0.01"))

            account.total_turnover = (_d(account.total_turnover) - all_product_summa).quantize(Decimal("0.01"))
            account.filial_debt = (_d(account.filial_debt) - delta_debt).quantize(Decimal("0.01"))

            # xohlasangiz 0 dan past tushirmay qo'ying:
            # if account.filial_debt < 0:
            #     account.filial_debt = Decimal("0.00")
            # if account.total_turnover < 0:
            #     account.total_turnover = Decimal("0.00")

            account.save(update_fields=["total_turnover", "filial_debt"])
            supplier_account_updated = True

    # 3) invoice itemlarini o'chirish (ProductHistory)
    deleted_items_count, _ = items_qs.delete()

    # 4) invoice ni o'chirish (hard delete)
    invoice.delete()

    return {
        "deleted_invoice_id": invoice_id,
        "deleted_items_count": deleted_items_count,
        "rolled_back_stock_rows": rolled_back_rows,
        "supplier_account_updated": supplier_account_updated,
        "all_product_summa": str(all_product_summa),
        "paid_total": str(paid_total),
    }