import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import ProductModel, ProductType


class Command(BaseCommand):
    help = "model_type.json dan ProductType'larni import qiladi (madel ProductModel.elegant_id bo'yicha bog'lanadi)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="inventory/data/model_type.json",
            help="BASE_DIR ga nisbatan JSON fayl yo'li (default: inventory/data/model_type.json)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="elegant_id bo'yicha bor bo'lsa update qiladi, bo'lmasa create qiladi.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) JSON path
        rel_path = options["file"]
        json_path = (Path(settings.BASE_DIR) / rel_path).resolve()

        if not json_path.exists():
            raise FileNotFoundError(
                f"JSON topilmadi: {json_path}\n"
                f"Tekshiring: {rel_path} fayli loyiha ichida mavjudmi?"
            )

        raw = json.loads(json_path.read_text(encoding="utf-8"))

        def to_int(v, default=None):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        # 2) JSONdagi sorting bo'yicha kichikdan kattaga saralash
        raw_sorted = sorted(raw, key=lambda x: to_int(x.get("sorting"), default=10**18))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        missing_model_count = 0

        # 3) Saralangan ro'yxat bo'yicha ProductType.sorting = 1..N
        for idx, item in enumerate(raw_sorted, start=1):
            elegant_id = to_int(item.get("id"))
            name = (item.get("name") or "").strip()
            brand_id = to_int(item.get("brand_id"))

            # minimal validatsiya
            if not elegant_id or not name or not brand_id:
                skipped_count += 1
                continue

            # 4) ProductModel ni elegant_id==brand_id bo'yicha topamiz (birinchisi)
            model_obj = (
                ProductModel.objects
                .filter(elegant_id=brand_id)
                .order_by("id")
                .only("id")
                .first()
            )

            if not model_obj:
                # topilmasa keyingisiga o'tkazib yuboramiz
                missing_model_count += 1
                continue

            defaults = {
                "name": name,
                "madel_id": model_obj.id,   # ✅ FK (ProductModel)
                "sorting": idx,             # ✅ 1 dan boshlab ketadi
                "is_delete": False,
            }

            if options["update"]:
                obj, created = ProductType.objects.update_or_create(
                    elegant_id=elegant_id,
                    defaults=defaults,
                )
                created_count += int(created)
                updated_count += int(not created)
            else:
                obj, created = ProductType.objects.get_or_create(
                    elegant_id=elegant_id,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    # mavjud bo'lsa ham sorting ketma-ket bo'lishi uchun yangilab qo'yamiz
                    ProductType.objects.filter(pk=obj.pk).update(**defaults)
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            "OK ✅ Import tugadi.\n"
            f"Created={created_count}, Updated={updated_count}, Skipped={skipped_count}, "
            f"MissingProductModel={missing_model_count}\n"
            f"JSON: {json_path}"
        ))
