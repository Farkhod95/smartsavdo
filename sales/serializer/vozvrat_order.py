from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from accounts.serializers import  FilialListSerializer
from inventory.models import ProductStock, Product
from sales.models import  VozvratOrder, Order, OrderHistoryProduct, Client
from sales.serializer.client import ClientListSerializer
from users.serializers import UserViewListShortSerializer


class VozvratOrderListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)
    employee_detail = UserViewListShortSerializer(source='employee', read_only=True)

    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'employee_detail', 'exchange_rate', 'date',
                  'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete',
                  'is_vazvrat_status', 'is_karzinka', 'created_time')


class VozvratOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client',
                  'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
                  'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete', 'is_vazvrat_status', 'is_karzinka')


class VozvratOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VozvratOrder
        fields = (
            'id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'old_total_debt_client', 'total_debt_client',
            'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
            'summa_terminal', 'summa_transfer', 'discount_amount',
            'is_delete', 'is_vazvrat_status', 'is_karzinka'
        )

    def _get_user_filial(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        filial = getattr(user, "order_filial", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Autentifikatsiya talab qilinadi."})

        if filial is None:
            raise serializers.ValidationError({"detail": "Sizga order_filial biriktirilmagan. (User.order_filial = null)"})

        return filial

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")

        # employee auto
        if validated_data.get("employee") is None and request and request.user.is_authenticated:
            validated_data["employee"] = request.user

        # OLD qiymatlar (delta uchun)
        old_instance_total_debt_client = instance.total_debt_client or Decimal("0")
        old_instance_summa_total_dollar = instance.summa_total_dollar or Decimal("0")

        # update qilamiz
        updated = super().update(instance, validated_data)

        # exchange_rate tekshirish
        exchange_rate = updated.exchange_rate or Decimal("0")
        if exchange_rate <= 0:
            raise serializers.ValidationError({"exchange_rate": "Kurs (exchange_rate) 0 dan katta bo‘lishi kerak."})

        # summa_total_dollar qayta hisoblash (Decimal)
        summa_total_dollar = (
            (updated.summa_dollar or Decimal("0"))
            + (updated.summa_naqt or Decimal("0")) / exchange_rate
            + (updated.summa_kilik or Decimal("0")) / exchange_rate
            + (updated.summa_terminal or Decimal("0")) / exchange_rate
            + (updated.summa_transfer or Decimal("0")) / exchange_rate
            - (updated.discount_amount or Decimal("0"))
        )
        updated.summa_total_dollar = summa_total_dollar

        # old_total_debt_client ni "snapshot" sifatida saqlamoqchi bo‘lsangiz:
        # bu qiymatni requestdan emas, instance old qarzidan oling:
        updated.old_total_debt_client = old_instance_total_debt_client

        updated.save(update_fields=["summa_total_dollar", "old_total_debt_client"])

        # Faqat is_karzinka=False bo‘lganda Order/Client balansiga tegamiz
        if updated.is_karzinka is False:
            if updated.client is None:
                raise serializers.ValidationError({"client": "client majburiy"})

            filial = self._get_user_filial()

            order = Order.objects.filter(client=updated.client, filial=filial).first()
            if not order:
                raise serializers.ValidationError({"detail": "Order topilmadi (client+filial bo‘yicha)."})

            # vozvrat product summasi (USD)
            total_vozvrat_product_summa = Decimal("0")
            products = OrderHistoryProduct.objects.filter(vozvrat_order_id=updated.id, is_delete=False)

            for p in products:
                cnt = Decimal(str(p.count or 0))
                total_vozvrat_product_summa += cnt * (p.price_dollar or Decimal("0"))

            # yangi total_debt_client (vozvrat bo‘yicha)
            # Sizning mantiqingizni saqlab:
            new_total_debt_client = old_instance_total_debt_client - (total_vozvrat_product_summa - updated.summa_total_dollar)

            # updated.total_debt_client ni o‘zgartirdik
            updated.old_total_debt_client = order.total_debt_client
            updated.total_debt_client = new_total_debt_client
            updated.save(update_fields=["total_debt_client"])

            # ✅ Delta (old -> new)
            delta = new_total_debt_client - old_instance_total_debt_client

            # Order va Client balanslarini faqat delta bo‘yicha yangilaymiz
            order.total_debt_old_client = order.total_debt_client
            order.total_debt_client = (order.total_debt_client or Decimal("0")) + delta
            order.save(update_fields=["total_debt_old_client", "total_debt_client"])

            client = updated.client
            client.total_debt = (client.total_debt or Decimal("0")) + delta
            client.save(update_fields=["total_debt"])

        return updated




class VozvratOrderReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = VozvratOrder
        fields = (
            'id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'old_total_debt_client', 'total_debt_client',
            'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
            'summa_terminal', 'summa_transfer', 'discount_amount',
            'is_delete', 'is_vazvrat_status', 'is_karzinka'
        )
        # bu 3ta fieldni biz update()da hisoblab qo'yamiz
        read_only_fields = ('old_total_debt_client', 'total_debt_client', 'summa_total_dollar')

    # ---------------- helpers ----------------

    def _get_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Autentifikatsiya talab qilinadi."})
        return user

    def _d(self, v) -> Decimal:
        if v is None or v == "":
            return Decimal("0")
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    def _q2(self, v: Decimal) -> Decimal:
        return (v or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _uzs_to_usd(self, uzs: Decimal, rate: Decimal) -> Decimal:
        rate = self._d(rate)
        if rate <= 0:
            raise serializers.ValidationError({"exchange_rate": "Kurs (exchange_rate) 0 dan katta bo‘lishi kerak."})
        return self._q2(self._d(uzs) / rate)

    def _calc_paid_usd(self, vo: VozvratOrder) -> Decimal:
        """
        Vozvrat bo'yicha mijozga qaytarilgan pul (USD):
          dollar + (naqt/kilik/terminal/transfer UZS->USD) - discount
        """
        rate = self._d(vo.exchange_rate)
        paid = (
            self._d(vo.summa_dollar)
            + self._uzs_to_usd(self._d(vo.summa_naqt), rate)
            + self._uzs_to_usd(self._d(vo.summa_kilik), rate)
            + self._uzs_to_usd(self._d(vo.summa_terminal), rate)
            + self._uzs_to_usd(self._d(vo.summa_transfer), rate)
            - self._d(vo.discount_amount)
        )
        return self._q2(paid)

    def _calc_products_usd(self, vo: VozvratOrder) -> Decimal:
        """
        Qaytgan tovarlar summasi (USD):
        - price_dollar bo'lsa -> USD
        - bo'lmasa price_sum / exchange_rate
        """
        rate = self._d(vo.exchange_rate)
        qs = OrderHistoryProduct.objects.filter(
            vozvrat_order_id=vo.id,
            is_delete=False
        ).select_related("product")

        total = Decimal("0")
        for p in qs:
            cnt = self._d(p.count or 0)

            if p.price_dollar and self._d(p.price_dollar) > 0:
                unit_usd = self._d(p.price_dollar)
            else:
                unit_usd = self._uzs_to_usd(self._d(p.price_sum), rate)

            total += cnt * unit_usd

        return self._q2(total)

    def _calc_effect_on_client_debt(self, vo: VozvratOrder) -> Decimal:
        """
        Client.total_debt ga ta'sir (net):
          effect = paid_usd - products_usd
        - paid_usd: siz mijozga pul berdingiz => debt oshishi ( + )
        - products_usd: tovar qaytdi => debt kamayishi ( - )
        """
        paid_usd = self._calc_paid_usd(vo)
        products_usd = self._calc_products_usd(vo)
        return self._q2(paid_usd - products_usd)

    def _apply_stock(self, vo: VozvratOrder, sign: int):
        """
        sign=+1  => confirm bo'lganda omborga qo'shamiz
        sign=-1  => rollback bo'lganda ombordan ayiramiz

        ⚠️ Bu funksiyani ishlatish uchun:
        - stock update item create/edit/delete'da qilinmasligi kerak (double bo'lmasin).
        """
        if sign not in (1, -1):
            return

        items = OrderHistoryProduct.objects.filter(
            vozvrat_order_id=vo.id,
            is_delete=False
        ).select_related("product", "sklad")

        for it in items:
            if not it.product_id:
                continue
            if not it.sklad_id:
                raise serializers.ValidationError({"sklad": "Vozvrat itemlarda sklad majburiy (OrderHistoryProduct.sklad)"})

            delta_qty = int(it.count or 0) * sign

            # Product lock
            prod = Product.objects.select_for_update(of=("self",)).get(pk=it.product_id)
            if prod.is_delete:
                raise serializers.ValidationError({"product": f"Product o'chirilgan: {prod.pk}"})

            # ProductStock lock + get_or_create
            stock, _ = ProductStock.objects.select_for_update().get_or_create(
                product_id=prod.pk,
                sklad_id=it.sklad_id,
                defaults={"count": 0}
            )

            # rollback bo'lsa minusga tushib ketmasin
            if delta_qty < 0:
                cur = int(stock.count or 0)
                if cur + delta_qty < 0:
                    raise serializers.ValidationError({
                        "stock": f"Ombor minus bo'lib ketadi. product={prod.pk}, sklad={it.sklad_id}, "
                                 f"ombor={cur}, ayirish={abs(delta_qty)}"
                    })

            # update stock
            ProductStock.objects.filter(pk=stock.pk).update(count=F("count") + delta_qty)

            # agar Product.count ham umumiy qoldiq bo'lsa
            if prod.count is not None:
                if delta_qty < 0:
                    curp = int(prod.count or 0)
                    if curp + delta_qty < 0:
                        raise serializers.ValidationError({
                            "product_count": f"Product.count minus bo'lib ketadi. product={prod.pk}, "
                                             f"count={curp}, ayirish={abs(delta_qty)}"
                        })
                Product.objects.filter(pk=prod.pk).update(count=F("count") + delta_qty)

    # ---------------- main update ----------------

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self._get_user()

        # 1) lock vozvrat order
        instance = VozvratOrder.objects.select_for_update(of=("self",)).get(pk=instance.pk)

        # employee auto
        if validated_data.get("employee") is None:
            validated_data["employee"] = instance.employee_id or user

        # old flags
        old_confirmed = bool(instance.is_vazvrat_status)
        old_is_karzinka = bool(instance.is_karzinka)

        # old effect (faqat confirmed bo'lsa ta'sir bergan deb hisoblaymiz)
        old_effect = self._calc_effect_on_client_debt(instance) if (old_confirmed and old_is_karzinka is False) else Decimal("0")

        # 2) update fields
        updated = super().update(instance, validated_data)

        # basic checks
        if self._d(updated.exchange_rate) <= 0:
            raise serializers.ValidationError({"exchange_rate": "Kurs (exchange_rate) 0 dan katta bo‘lishi kerak."})

        if updated.client_id is None:
            raise serializers.ValidationError({"client": "client majburiy."})

        # 3) lock client
        client = Client.objects.select_for_update().get(pk=updated.client_id)

        # 4) recompute paid_total_usd -> summa_total_dollar
        paid_total_usd = self._calc_paid_usd(updated)
        updated.summa_total_dollar = paid_total_usd

        # snapshot fields
        updated.old_total_debt_client = self._q2(self._d(client.total_debt))

        # 5) new flags
        new_confirmed = bool(updated.is_vazvrat_status)
        new_is_karzinka = bool(updated.is_karzinka)

        # Draft (karzinka) bo'lsa balansga ham, stockga ham tegmaymiz
        # faqat summa_total_dollar va old_total_debt_client ni saqlaymiz
        if new_is_karzinka is not False:
            updated.total_debt_client = self._q2(self._d(client.total_debt))
            updated.save(update_fields=["summa_total_dollar", "old_total_debt_client", "total_debt_client"])
            return updated

        # 6) new effect (faqat confirmed bo'lsa)
        new_effect = self._calc_effect_on_client_debt(updated) if new_confirmed else Decimal("0")

        # 7) delta for client debt (idempotent!)
        delta_effect = self._q2(new_effect - old_effect)

        if delta_effect != 0:
            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") + delta_effect)

        # 8) STOCK: faqat status transition bo'lsa qo'llaymiz
        #    - old False -> new True  : stock +count
        #    - old True  -> new False : stock -count
        #    - True -> True / False -> False : stockga tegmaymiz
        #
        # ⚠️ Agar confirmed holatda productlar (count) o'zgarsa,
        #    bu serializer stock delta'ni bilmaydi (snapshot yo'q).
        #    Shuning uchun tavsiya:
        #    - confirmed bo'lsa vozvrat item PUT/DELETE ni blok qiling,
        #      yoki "unconfirm -> edit -> confirm" qiling.
        if (not old_confirmed) and new_confirmed:
            self._apply_stock(updated, sign=+1)
        elif old_confirmed and (not new_confirmed):
            self._apply_stock(updated, sign=-1)

        # 9) updated.total_debt_client ni “after” qilib yozib qo'yamiz
        client.refresh_from_db(fields=["total_debt"])
        updated.total_debt_client = self._q2(self._d(client.total_debt))

        updated.save(update_fields=[
            "summa_total_dollar",
            "old_total_debt_client",
            "total_debt_client",
        ])

        return updated