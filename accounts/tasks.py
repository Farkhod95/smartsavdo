from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

from .models import Note


@shared_task(bind=True)
def check_note_deadlines(self):
    """
    TALAB:
    - hozirgi vaqtdan 1 soat ichida deadline bo'ladigan Note'lar uchun notification yuborish
      (faqat 1 marta shart emas -> har run'da yuboradi)
    - muddati o'tsa -> status EXPIRED + xabar (har run'da qayta yubormaydi, chunki status EXPIRED bo'lib qoladi)
    - Celery logda None bo'lmasin -> result return qiladi
    """

    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)
    channel_layer = get_channel_layer()

    qs = (
        Note.objects
        .filter(is_delete=False)
        .exclude(status=Note.STATUS.DONE)
    )

    checked = 0
    skipped_no_date = 0
    sent_1hour = 0
    expired_set = 0
    errors = 0

    print(f"\n[check_note_deadlines] now={now.isoformat()} notes_count={qs.count()}")

    # 1) date yo'q bo'lganlar
    skipped_no_date = qs.filter(date__isnull=True).count()

    # 2) muddati o'tganlar -> EXPIRED (EXPIRED bo'lsa qayta yubormaydi)
    expired_qs = qs.filter(date__isnull=False, date__lte=now).exclude(status=Note.STATUS.EXPIRED)
    for note in expired_qs.iterator():
        checked += 1
        try:
            note.status = Note.STATUS.EXPIRED
            note.save(update_fields=["status"])
            expired_set += 1

            _send_note_notification(
                channel_layer=channel_layer,
                note=note,
                event_type="expired",
                title="Muddat tugadi",
                message="Note muddati tugadi",
            )
        except Exception as e:
            errors += 1
            print(f"[check_note_deadlines] EXPIRED Note ID={getattr(note, 'id', None)} error: {e}")

    # 3) hozirgi vaqtdan 1 soat ichida bo'ladiganlar -> har run'da yuboradi
    soon_1h_qs = qs.filter(
        date__isnull=False,
        date__gt=now,
        date__lte=one_hour_from_now,
    )

    for note in soon_1h_qs.iterator():
        checked += 1
        try:
            _send_note_notification(
                channel_layer=channel_layer,
                note=note,
                event_type="deadline_1hour",
                title="Ogohlantirish",
                message="Eslatma muddati tugashiga 1 soatdan kam qoldi",
            )
            sent_1hour += 1
        except Exception as e:
            errors += 1
            print(f"[check_note_deadlines] 1H Note ID={getattr(note, 'id', None)} error: {e}")

    return {
        "now": now.isoformat(),
        "notes_count": qs.count(),
        "checked": checked,
        "skipped_no_date": skipped_no_date,
        "sent_1hour": sent_1hour,
        "expired_set": expired_set,
        "errors": errors,
        "window_1hour_to": one_hour_from_now.isoformat(),
    }


def _send_note_notification(channel_layer, note: Note, event_type: str, title: str, message: str) -> None:
    if not channel_layer:
        print("[note_notification] channel_layer yo'q")
        return

    metric_data = {
        "event": event_type,
        "note_id": note.id,
        "title": title,
        "message": message,
        "note_title": note.title or "",
        "deadline": note.date.isoformat() if note.date else None,
        "status": note.status,
    }

    try:
        print(f"[note_notification] SEND -> {metric_data}")
        async_to_sync(channel_layer.group_send)(
            "metrics_group",
            {
                "type": "metric",
                "metric": metric_data,
            }
        )
    except Exception as e:
        print(f"[note_notification] Note ID={getattr(note, 'id', None)} websocket error: {e}")