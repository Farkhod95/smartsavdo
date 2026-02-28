from decimal import Decimal
from django.db import transaction
from django.db.models import F, Sum

from inventory.models import ProductHistory, ProductStock, Product
from suppliers.models import PurchaseInvoice, SupplierAccount


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
    ✅ 100% ishlaydi (Postgres FOR UPDATE join muammosiz):
    - Invoice lock
    - ProductHistory rows lock (HECH QANDAY select_related YO'Q)
    - Stock rollback
    - SupplierAccount rollback (EXTERNAL bo'lsa)
    - ProductHistory delete
    - Invoice delete
    """

    # 1) Invoice lock
    invoice = (
        PurchaseInvoice.objects
        .select_for_update()
        .get(pk=invoice_id)
    )

    # 2) Itemlar (LOCK) — MUHIM: select_related QILMAYMIZ!
    items_qs = (
        ProductHistory.objects
        .select_for_update()
        .filter(purchase_invoice_id=invoice.id)
    )

    # summa va qty
    agg = items_qs.aggregate(
        total_qty=Sum("count"),
        total_sum=Sum(F("real_price") * F("count")),
    )
    all_product_summa = _d(agg.get("total_sum") or 0).quantize(Decimal("0.01"))
    paid_total = _calc_paid_total(invoice).quantize(Decimal("0.01"))

    incoming_sklad_id = invoice.sklad_id
    outgoing_sklad_id = invoice.sklad_outgoing_id if invoice.type == PurchaseInvoice.TYPE.INTERNAL else None

    rolled_back_rows = 0
    touched_product_ids = set()

    # 3) STOCK rollback
    # (join qilmaslik uchun values() bilan olamiz)
    for row in items_qs.values("id", "product_id", "count"):
        qty = int(row["count"] or 0)
        if qty == 0:
            continue

        product_id = row["product_id"]
        if not product_id:
            # history’da product null bo‘lsa rollback qilolmaymiz
            continue

        touched_product_ids.add(product_id)

        # incoming sklad’dan ayiramiz
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

        # internal bo‘lsa outgoing sklad’ga qaytaramiz
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

    # 4) Product.count ni qayta hisoblash (har bir product bo‘yicha)
    # join qilmaymiz, alohida olib kelamiz
    for p in Product.objects.filter(id__in=touched_product_ids).select_for_update():
        if hasattr(p, "recalc_count_from_stocks"):
            p.recalc_count_from_stocks(save=True)

    # 5) SupplierAccount rollback (faqat EXTERNAL)
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

            account.save(update_fields=["total_turnover", "filial_debt"])
            supplier_account_updated = True

    # 6) invoice itemlarini o‘chirish (ProductHistory)
    deleted_items_count, _ = items_qs.delete()

    # 7) invoice ni o‘chirish (hard delete)
    invoice.delete()

    return {
        "deleted_invoice_id": invoice_id,
        "deleted_items_count": deleted_items_count,
        "rolled_back_stock_rows": rolled_back_rows,
        "supplier_account_updated": supplier_account_updated,
        "all_product_summa": str(all_product_summa),
        "paid_total": str(paid_total),
    }