# sales/tasks.py

from datetime import datetime, time

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from sales.models import OrderHistory, OrderHistoryProduct


@shared_task
def delete_expired_karzinka_order_histories():
    """
    Har kuni 02:00 da ishga tushadi.
    BUGUNGI karzinkalarga tegmaydi.
    Faqat bugun 00:00 dan OLDIN yaratilgan (kechagi va undan oldingi) is_karzinka=True larni o'chiradi.
    """

    # Bugun sanasi (Asia/Tashkent timezone bo'yicha)
    today = timezone.localdate()

    # Bugun 00:00 (timezone-aware)
    today_start = timezone.make_aware(datetime.combine(today, time.min))

    qs = OrderHistory.objects.filter(
        is_delete=False,
        is_karzinka=True,
        created_time__lt=today_start,   # <-- MUHIM: bugungi kundagiga tegmaydi
    )

    with transaction.atomic():
        expired_ids = list(qs.values_list('id', flat=True))

        if not expired_ids:
            return {"deleted_count": 0, "deleted_ids": []}

        # Avval productlarni o'chiramiz (orphan bo'lib qolmasin)
        products_deleted, _ = OrderHistoryProduct.objects.filter(
            order_history_id__in=expired_ids
        ).delete()

        # Keyin order_history larni o'chiramiz
        histories_deleted, _ = OrderHistory.objects.filter(id__in=expired_ids).delete()

    return {
        "deleted_order_histories": histories_deleted,
        "deleted_order_history_products": products_deleted,
        "deleted_ids": expired_ids
    }