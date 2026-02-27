from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from suppliers.models import SupplierDebtRepayment, SupplierAccount


def _d(val) -> Decimal:
    try:
        return Decimal(val or 0)
    except Exception:
        return Decimal("0")


def _paid_total_from_validated(data: dict) -> Decimal:
    """
    total bo'lmasa parts yig'indisini oladi
    """
    parts = (
        _d(data.get("summa_dollar")) +
        _d(data.get("summa_naqt")) +
        _d(data.get("summa_kilik")) +
        _d(data.get("summa_terminal")) +
        _d(data.get("summa_transfer"))
    )
    total = _d(data.get("summa_total_dollar"))
    if total <= 0 and parts > 0:
        total = parts
    return total.quantize(Decimal("0.01"))


@transaction.atomic
def update_supplier_debt_repayment(*, repayment_id: int, validated_data: dict, user) -> SupplierDebtRepayment:
    """
    Repayment edit:
    1) eski repayment ta'sirini rollback: debt += old_paid
    2) yangi repayment ta'sirini apply: debt -= new_paid
    3) repayment.total_debt_old / total_debt ni qayta yozadi
    """
    repayment = (
        SupplierDebtRepayment.objects
        .select_for_update()
        .select_related("supplier")
        .get(pk=repayment_id)
    )

    if not repayment.supplier_id:
        raise ValueError("Repayment supplier bo'sh bo'lmasligi kerak.")

    # SupplierAccount lock
    account, _ = SupplierAccount.objects.select_for_update().get_or_create(
        supplier_id=repayment.supplier_id,
        defaults={"total_turnover": 0, "filial_debt": 0},
    )

    # --- 1) ESKI to'lovni rollback ---
    old_paid = _d(repayment.summa_total_dollar).quantize(Decimal("0.01"))
    current_debt = _d(account.filial_debt).quantize(Decimal("0.01"))

    # rollback: qarzga qaytariladi
    debt_after_rollback = (current_debt + old_paid).quantize(Decimal("0.01"))

    # --- 2) YANGI to'lovni apply ---
    new_paid = _paid_total_from_validated(validated_data)

    if new_paid <= 0:
        raise ValueError("To'lov summasi 0 dan katta bo'lishi kerak.")

    # avans yo'q: new_paid rollbackdan keyingi qarzdan katta bo'lmasin
    if new_paid > debt_after_rollback:
        raise ValueError(f"To‘lov ({new_paid}) qarzdan ({debt_after_rollback}) katta bo‘lishi mumkin emas.")

    new_debt = (debt_after_rollback - new_paid).quantize(Decimal("0.01"))

    # --- 3) Account yangilash ---
    account.filial_debt = new_debt
    account.save(update_fields=["filial_debt"])

    # repayment fields yangilash (employee ni o'zgartirmaymiz)
    for f in ("date", "summa_total_dollar", "summa_dollar", "summa_naqt", "summa_kilik", "summa_terminal", "summa_transfer"):
        if f in validated_data:
            setattr(repayment, f, validated_data.get(f))

    # total bo'lmasa parts yig'indisini yozib qo'yamiz
    repayment.summa_total_dollar = new_paid

    repayment.total_debt_old = debt_after_rollback
    repayment.total_debt = new_debt
    repayment.updated_by = user
    repayment.save()

    return repayment


@transaction.atomic
def delete_supplier_debt_repayment(*, repayment_id: int, user) -> dict:
    """
    Repayment delete:
    - Account debt rollback: debt += repayment.paid_total
    - repayment delete
    """
    repayment = (
        SupplierDebtRepayment.objects
        .select_for_update()
        .get(pk=repayment_id)
    )

    if not repayment.supplier_id:
        # supplier bo'lmasa oddiy delete
        repayment.delete()
        return {"deleted_id": repayment_id, "account_updated": False}

    account, _ = SupplierAccount.objects.select_for_update().get_or_create(
        supplier_id=repayment.supplier_id,
        defaults={"total_turnover": 0, "filial_debt": 0},
    )

    paid = _d(repayment.summa_total_dollar).quantize(Decimal("0.01"))
    account.filial_debt = (_d(account.filial_debt) + paid).quantize(Decimal("0.01"))
    account.save(update_fields=["filial_debt"])

    repayment.delete()
    return {"deleted_id": repayment_id, "account_updated": True, "rolled_back": str(paid)}