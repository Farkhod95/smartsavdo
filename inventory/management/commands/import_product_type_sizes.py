import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import ProductType, ProductTypeSize, Unit


class Command(BaseCommand):
    help = "brands_size.json dan ProductTypeSize'larni import qiladi (ProductType.elegant_id orqali bog'laydi)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="inventory/data/brands_size.json",
            help="BASE_DIR ga nisbatan JSON fayl yo'li (default: inventory/data/brands_size.json)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Agar product_type + size + unit kombinatsiyasi mavjud bo'lsa update, bo'lmasa create qiladi.",
        )
        parser.add_argument(
            "--skip-missing-unit",
            action="store_true",
            help="Unit topilmasa ham skip qiladi (default: unit=None qilib saqlaydi).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
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

        def to_float(v, default=None):
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        # Sorting (barqaror tartib): product_category_id, size, id
        raw_sorted = sorted(
            raw,
            key=lambda x: (
                to_int(x.get("product_category_id"), 10**18),
                to_float(x.get("size"), 10**18),
                to_int(x.get("id"), 10**18),
            ),
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        missing_type_count = 0
        missing_unit_count = 0

        sort_counter = 1

        for item in raw_sorted:
            product_category_id = to_int(item.get("product_category_id"))
            size_value = to_float(item.get("size"))
            unit_type = to_int(item.get("type"))

            # minimal validatsiya
            if not product_category_id or size_value is None:
                skipped_count += 1
                continue

            # 1) ProductType topish: elegant_id == product_category_id
            product_type_obj = (
                ProductType.objects
                .filter(elegant_id=product_category_id)
                .order_by("id")
                .only("id")
                .first()
            )
            if not product_type_obj:
                missing_type_count += 1
                continue  # topilmasa o'tkazib yuboriladi

            # 2) Unit topish: Unit.id == type
            unit_obj = None
            if unit_type is not None:
                unit_obj = (
                    Unit.objects
                    .filter(id=unit_type)
                    .order_by("id")
                    .only("id")
                    .first()
                )

            if unit_obj is None:
                missing_unit_count += 1
                if options["skip_missing_unit"]:
                    continue  # xohlasangiz unit topilmasa ham skip

            defaults = {
                "product_type_id": product_type_obj.id,
                "size": size_value,
                "unit_id": unit_obj.id if unit_obj else None,
                "sorting": sort_counter,
                "is_delete": False,
            }

            # Update/Create logikasi:
            # (product_type, size, unit) bo'yicha takror bo'lmasin deb shuni uniq sifatida ishlatyapmiz
            lookup = {
                "product_type_id": product_type_obj.id,
                "size": size_value,
                "unit_id": unit_obj.id if unit_obj else None,
            }

            if options["update"]:
                obj, created = ProductTypeSize.objects.update_or_create(
                    **lookup,
                    defaults=defaults,
                )
                created_count += int(created)
                updated_count += int(not created)
            else:
                obj, created = ProductTypeSize.objects.get_or_create(
                    **lookup,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    ProductTypeSize.objects.filter(pk=obj.pk).update(**defaults)
                    updated_count += 1

            sort_counter += 1

        self.stdout.write(self.style.SUCCESS(
            "OK ✅ ProductTypeSize import tugadi.\n"
            f"Created={created_count}, Updated={updated_count}, Skipped={skipped_count}, "
            f"MissingProductType={missing_type_count}, MissingUnit={missing_unit_count}\n"
            f"JSON: {json_path}"
        ))
