import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import ProductModel  # kerak bo'lsa import path'ni moslang
# Agar ProductBranch modeli boshqa appda bo'lsa, uni tekshirib ko'rishingiz mumkin:
# from inventory.models import ProductBranch


class Command(BaseCommand):
    help = "brand.json dan ProductModel'larni sorting bo'yicha saralab import qiladi (sorting=1..N)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--branch-id",
            type=int,
            default=1,
            help="ProductBranch ID (default: 1)",
        )
        parser.add_argument(
            "--file",
            type=str,
            default="inventory/data/brand.json",
            help="JSON fayl yo'li (default: inventory/data/brand.json)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Agar elegant_id bo'yicha mavjud bo'lsa yangilab qo'yadi (update_or_create).",
        )
        parser.add_argument(
            "--skip-deleted",
            action="store_true",
            help="is_delete=True qilib qo'ymaydi (default: is_delete=False saqlanadi).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        branch_id = options["branch_id"]
        json_path = Path(options["file"])
        do_update = options["update"]
        skip_deleted = options["skip_deleted"]

        if not json_path.exists():
            raise FileNotFoundError(f"JSON topilmadi: {json_path}")

        # JSON o'qish
        raw = json.loads(json_path.read_text(encoding="utf-8"))

        # sorting ni int qilib, kichigidan kattaga saralash
        def to_int(v, default=10**18):
            try:
                return int(v)
            except (TypeError, ValueError):
                return default

        raw_sorted = sorted(raw, key=lambda x: to_int(x.get("sorting")))

        created_count = 0
        updated_count = 0

        # JSON saralangan tartibda ProductModel.sorting ni 1..N qilib ketkazamiz
        for idx, item in enumerate(raw_sorted, start=1):
            elegant_id = to_int(item.get("id"), default=None)
            name = (item.get("name") or "").strip()

            if elegant_id is None or not name:
                # yaroqsiz qatordan o'tib ketamiz
                continue

            defaults = {
                "name": name,
                "branch_id": branch_id,
                "sorting": idx,          # 1 dan boshlab nomeratsiya
                "is_delete": False if not skip_deleted else False,
            }

            if do_update:
                obj, created = ProductModel.objects.update_or_create(
                    elegant_id=elegant_id,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            else:
                # update qilmasdan: faqat yo'q bo'lsa yaratadi
                obj, created = ProductModel.objects.get_or_create(
                    elegant_id=elegant_id,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    # mavjud bo'lsa ham sortingni ketma-ket qilish kerak bo'lsa, uni ham yangilab qo'yamiz
                    # (siz talab qilgan "1 dan boshlab" qoidasi uchun)
                    obj.name = defaults["name"]
                    obj.branch_id = defaults["branch_id"]
                    obj.sorting = defaults["sorting"]
                    obj.is_delete = defaults["is_delete"]
                    obj.save(update_fields=["name", "branch_id", "sorting", "is_delete"])
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import yakunlandi. Created: {created_count}, Updated: {updated_count}, Branch ID: {branch_id}"
        ))
