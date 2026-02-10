# inventory/management/commands/import_products_from_warehouse.py

import json
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Product, ProductModel, ProductType, ProductTypeSize, Unit


class Command(BaseCommand):
    help = "warehouse.json dan Product larni import qiladi (ProductModel/ProductType/ProductTypeSize orqali bog'laydi)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=None,
            help="warehouse.json yo'li. Masalan: inventory/data/warehouse.json",
        )
        parser.add_argument(
            "--filial",
            type=int,
            default=1,
            help="Product.filial_id (default=1)",
        )
        parser.add_argument(
            "--branch",
            type=int,
            default=1,
            help="Product.branch_id (default=1)",
        )
        parser.add_argument(
            "--reserve",
            type=int,
            default=100,
            help="Product.reserve_limit (default=100)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=1000,
            help="Product.count (default=1000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Saqlamasdan tekshiradi (faqat log).",
        )

    def _guess_json_path(self):
        """
        Avval inventory/data/warehouse.json ni qidiradi.
        Keyin BASE_DIR/inventory/data/warehouse.json ni qidiradi.
        """
        candidates = []

        # 1) inventory app ichidagi data papka
        # inventory/management/commands/... -> inventory/
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # inventory/
        candidates.append(os.path.join(app_dir, "data", "warehouse.json"))

        # 2) BASE_DIR dan
        candidates.append(os.path.join(settings.BASE_DIR, "inventory", "data", "warehouse.json"))

        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _to_int(self, v, default=None):
        if v is None:
            return default
        try:
            return int(str(v).strip())
        except Exception:
            return default

    def _to_float(self, v, default=None):
        if v is None:
            return default
        try:
            return float(str(v).strip().replace(",", "."))
        except Exception:
            return default

    def _to_decimal(self, v, default=Decimal("0")):
        if v is None:
            return default
        try:
            return Decimal(str(v).strip().replace(",", "."))
        except (InvalidOperation, ValueError):
            return default

    def _to_date(self, v):
        """
        cr_date format: YYYY-MM-DD
        """
        if not v:
            return None
        try:
            return datetime.strptime(str(v).strip(), "%Y-%m-%d").date()
        except Exception:
            return None

    @transaction.atomic
    def handle(self, *args, **options):
        json_path = options["path"] or self._guess_json_path()

        # Sizda fayl upload qilingan bo'lishi mumkin, lekin loyihada yo'q bo'lsa
        # shuni ham sinab ko'ramiz (dev muhitlar uchun):
        if not json_path:
            # /mnt/data da bo'lsa
            fallback = "/mnt/data/3517588d-c22a-43b7-b76b-6406552c5108.json"
            if os.path.exists(fallback):
                json_path = fallback

        if not json_path or not os.path.exists(json_path):
            raise FileNotFoundError(
                f"JSON topilmadi. --path bilan aniq ko'rsating. Masalan: inventory/data/warehouse.json"
            )

        filial_id = options["filial"]
        branch_id = options["branch"]
        reserve_limit = options["reserve"]
        default_count = options["count"]
        dry_run = options["dry_run"]

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("warehouse.json list ([]) bo'lishi kerak!")

        created = 0
        updated = 0
        skipped = 0

        for row in data:
            # warehouse.json maydonlari:
            # id, brand_id, product_category_id, size, cr_date, price, type, created_by ...
            wid = self._to_int(row.get("id"))
            brand_id = self._to_int(row.get("brand_id"))
            product_category_id = self._to_int(row.get("product_category_id"))
            size_val = self._to_float(row.get("size"))
            unit_type_id = self._to_int(row.get("type"))  # Unit.id deb ishlatyapmiz
            cr_date = self._to_date(row.get("cr_date"))
            price = self._to_decimal(row.get("price"), default=Decimal("0"))
            created_by_id = self._to_int(row.get("created_by"), default=None)

            # minimal validatsiya
            if not wid or not brand_id or not product_category_id or size_val is None or not unit_type_id:
                skipped += 1
                continue

            # 1) model (ProductModel) topish: elegant_id = brand_id
            model_obj = ProductModel.objects.filter(elegant_id=brand_id).first()
            if not model_obj:
                skipped += 1
                continue

            # 2) type (ProductType) topish: elegant_id = product_category_id
            type_obj = ProductType.objects.filter(elegant_id=product_category_id).first()
            if not type_obj:
                skipped += 1
                continue

            # 3) unit topish: Unit.id = warehouse.json type
            unit_obj = Unit.objects.filter(id=unit_type_id).first()
            if not unit_obj:
                skipped += 1
                continue

            # 4) size topish:
            # ProductTypeSize: product_type__elegant_id = product_category_id
            #                size = warehouse.size
            #                unit = Unit.id (warehouse.type)
            pts = ProductTypeSize.objects.filter(
                product_type__elegant_id=product_category_id,
                size=size_val,
                unit_id=unit_obj.id,
            ).first()
            if not pts:
                skipped += 1
                continue

            # idempotent kalit: note ichida warehouse id ni saqlab ketamiz
            note_key = f"imported_from_warehouse:{wid}"

            defaults = dict(
                date=cr_date,
                reserve_limit=reserve_limit,
                filial_id=filial_id,
                branch_id=branch_id,
                model_id=model_obj.id,
                type_id=type_obj.id,
                size_id=pts.id,
                count=default_count,
                real_price=price,
            )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY] wid={wid} model={model_obj.id} type={type_obj.id} size={pts.id} price={price}"
                    )
                )
                continue

            obj, is_created = Product.objects.update_or_create(
                note=note_key,
                defaults={
                    **defaults,
                    "note": note_key,
                },
            )

            # created_by ni ham to'ldirib qo'yamiz (xohlasangiz olib tashlaysiz)
            if created_by_id and obj.created_by_id is None:
                obj.created_by_id = created_by_id
                obj.save(update_fields=["created_by"])

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Import tugadi. created={created}, updated={updated}, skipped={skipped}"))
        self.stdout.write(self.style.SUCCESS(f"📄 JSON: {json_path}"))
