# finance/tasks.py
from __future__ import annotations

from celery import shared_task
from django.db import transaction

from finance.models import ExchangeRate


@shared_task(bind=True)
def deactivate_all_exchange_rates(self) -> dict:
    """
    Har kuni 01:00 da:
    - hamma ExchangeRate larni is_active=False qiladi
    """
    with transaction.atomic():
        updated = ExchangeRate.objects.filter(is_active=True).update(is_active=False)

    return {"deactivated_count": updated}