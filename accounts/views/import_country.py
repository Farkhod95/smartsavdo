from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pathlib import Path
import json

from ..models import Country


class CountryFileImportView(APIView):
    FILE_NAME = "countr_json.json"

    def _load_items_from_file(self):
        # /accounts/views/import_country.py -> parent (views) -> parent (accounts) -> data/countr_json.json
        data_path = Path(__file__).resolve().parent.parent / "data" / self.FILE_NAME
        if not data_path.exists():
            raise FileNotFoundError(f"{data_path} topilmadi")

        try:
            with data_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON xato: {e}")

        # Fayl to‘g‘ridan-to‘g‘ri list qaytaryapti
        items = payload.get("items") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise ValueError("Kutilgan format: ro‘yxat yoki {'items': [...]}")

        return items, str(data_path)

    def _do_import(self, items):
        created = updated = skipped = 0
        errors = []

        for idx, raw in enumerate(items, start=1):
            raw_id = raw.get("ID") or raw.get("id") or raw.get("code")
            if not raw_id:
                skipped += 1
                errors.append({"index": idx, "reason": "ID yo‘q", "item": raw})
                continue

            code = str(raw_id).strip()

            defaults = {
                "name": raw.get("name_uz") or raw.get("name") or "",
                "name_en": raw.get("name_en") or "",
                "name_uz": raw.get("name_uz") or "",
                "name_ru": raw.get("name_ru") or "",
            }

            try:
                obj, is_created = Country.objects.update_or_create(
                    code=code,
                    defaults=defaults,
                )
                if is_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({"index": idx, "reason": str(e), "item": raw})

        return created, updated, skipped, errors

    @transaction.atomic
    def post(self, request):
        try:
            items, file_used = self._load_items_from_file()
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        created, updated, skipped, errors = self._do_import(items)
        return Response(
            {
                "file": file_used,
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
                "total": len(items),
            },
            status=status.HTTP_200_OK,
        )
