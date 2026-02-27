# sales/tasks.py

from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from sales.models import OrderHistory, OrderHistoryProduct


@shared_task
def close_expired_karzinka_order_histories():
    """
    Har kuni 02:00 da ishga tushadi.
    1 kundan oshib ketgan is_karzinka=True OrderHistory larni yopadi (is_karzinka=False).
    """
    now = timezone.now()
    cutoff = now - timedelta(days=1)

    # BaseModel'dagi created_time sizda bor (indexda ishlatyapsiz)
    qs = OrderHistory.objects.filter(
        is_delete=False,
        is_karzinka=True,
        created_time__lte=cutoff,
    )

    with transaction.atomic():
        # Avval OH larni toplab, pk larini olib olamiz
        expired_ids = list(qs.values_list('id', flat=True))

        if not expired_ids:
            return {"closed_count": 0, "closed_ids": []}

        # OrderHistoryProduct ichida is_karzinka=True bo'lsa ham yopib qo'yamiz (ixtiyoriy, foydali)
        OrderHistoryProduct.objects.filter(
            order_history_id__in=expired_ids,
            is_delete=False,
            is_karzinka=True,
        ).update(is_karzinka=False)

        # OrderHistory yopiladi
        OrderHistory.objects.filter(id__in=expired_ids).update(is_karzinka=False)

    return {"closed_count": len(expired_ids), "closed_ids": expired_ids}