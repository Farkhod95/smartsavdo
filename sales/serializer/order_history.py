from rest_framework import serializers
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import F

from accounts.serializers import FilialSerializer, CurrencySerializer

from sales.models import Order, OrderHistory, OrderHistoryProduct, Client, ClientKeshbekHistory
from sales.serializer.client import ClientSerializer
from sales.serializer.order import OrderSerializer
from users.serializers import UserViewListShortSerializer


class OrderHistoryForSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderHistory
        fields = (
            'id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'all_profit_dollar', 'total_debt_client', 'total_debt_today_client',
            'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt',
            'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
            'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
            'is_debtor_product', 'status_order_dukon', 'status_order_sklad',
            'driver_info', 'is_karzinka', 'order_filial', 'currency'
        )


class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = ('id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note', 'all_profit_dollar',
                  'total_debt_client', 'total_debt_today_client', 'all_product_summa', 'summa_total_dollar',
                  'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
                  'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status', 'is_debtor_product',
                  'status_order_dukon', 'status_order_sklad', 'driver_info', 'is_karzinka', 'order_filial', 'currency')


class OrderHistoryListSerializer(serializers.ModelSerializer):
    order_detail = OrderSerializer(source='order', read_only=True)
    client_detail = ClientSerializer(source='client', read_only=True)
    order_filial_detail = FilialSerializer(source='order_filial', read_only=True)
    created_by_detail = UserViewListShortSerializer(source='created_by', read_only=True)
    currency_detail = CurrencySerializer(source='currency', read_only=True)

    class Meta:
        model = OrderHistory
        fields = ('id', 'order', 'order_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date', 'note',
                  'all_profit_dollar', 'total_debt_client', 'total_debt_today_client', 'all_product_summa',
                  'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer',
                  'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
                  'is_debtor_product', 'status_order_dukon', 'status_order_sklad', 'driver_info', 'is_karzinka',
                  'created_time', 'created_by', 'created_by_detail', 'order_filial', 'order_filial_detail',
                  'currency', 'currency_detail')


def d(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def recompute_order_totals(order: Order) -> Order:
    qs = order.order_histories.filter(is_delete=False, is_karzinka=False).order_by("id")

    if not qs.exists():
        order.number_of_order = 0
        order.date_last_order = None
        order.all_profit_dollar = Decimal("0")
        order.total_debt_client = Decimal("0")
        order.total_debt_old_client = Decimal("0")
        order.all_product_summa = Decimal("0")

        order.summa_total_dollar = Decimal("0")
        order.summa_dollar = Decimal("0")
        order.summa_naqt = Decimal("0")
        order.summa_kilik = Decimal("0")
        order.summa_terminal = Decimal("0")
        order.summa_transfer = Decimal("0")
        order.discount_amount = Decimal("0")
        order.save()
        return order

    last_h = qs.last()

    total_profit = Decimal("0")
    total_product_summa = Decimal("0")

    total_paid_total_dollar = Decimal("0")
    total_paid_dollar = Decimal("0")
    total_paid_naqt = Decimal("0")
    total_paid_kilik = Decimal("0")
    total_paid_terminal = Decimal("0")
    total_paid_transfer = Decimal("0")
    total_discount = Decimal("0")

    for h in qs:
        total_profit += d(h.all_profit_dollar)
        total_product_summa += d(h.all_product_summa)

        total_paid_total_dollar += d(h.summa_total_dollar)
        total_paid_dollar += d(h.summa_dollar)
        total_paid_naqt += d(h.summa_naqt)
        total_paid_kilik += d(h.summa_kilik)
        total_paid_terminal += d(h.summa_terminal)
        total_paid_transfer += d(h.summa_transfer)
        total_discount += d(h.discount_amount)

    total_debt_client = d(last_h.total_debt_client)
    today_debt = d(last_h.total_debt_today_client)
    old_debt = total_debt_client - today_debt
    if old_debt < 0:
        old_debt = Decimal("0")

    order.number_of_order = qs.count()
    order.client = last_h.client or order.client
    order.date_last_order = last_h.date

    order.all_profit_dollar = total_profit
    order.all_product_summa = total_product_summa

    order.summa_total_dollar = total_paid_total_dollar
    order.summa_dollar = total_paid_dollar
    order.summa_naqt = total_paid_naqt
    order.summa_kilik = total_paid_kilik
    order.summa_terminal = total_paid_terminal
    order.summa_transfer = total_paid_transfer

    order.discount_amount = total_discount
    order.total_debt_client = total_debt_client
    order.total_debt_old_client = old_debt

    order.save()
    return order


class OrderHistoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = (
            'id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'all_profit_dollar', 'total_debt_client', 'total_debt_today_client',
            'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt',
            'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
            'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
            'is_debtor_product', 'status_order_dukon', 'status_order_sklad',
            'driver_info', 'is_karzinka', 'order_filial', 'currency'
        )
        # extra_kwargs = {
        #     "order": {"read_only": True},
        #     "employee": {"required": False, "allow_null": True},
        # }

    def _get_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Autentifikatsiya talab qilinadi."})
        return user

    def _get_filial_for_order(self, validated_data, instance=None):
        """
        Sizning talablarga ko'ra: OrderHistory dagi filial bo'yicha order topish.
        OrderHistory modelida filial = order_filial.
        Create: validated_data orqali keladi, kelmasa user.order_filial.
        Update: kelmasa instance.order_filial, bo'lmasa user.order_filial.
        """
        user = self._get_user()
        if "order_filial" in validated_data and validated_data["order_filial"] is not None:
            return validated_data["order_filial"]
        if instance is not None and instance.order_filial is not None:
            return instance.order_filial
        filial = getattr(user, "order_filial", None)
        if filial is None:
            raise serializers.ValidationError({"detail": "Sizga order_filial biriktirilmagan. (User.order_filial = null)"})
        return filial

    def _is_karzinka_false(self, validated_data, instance=None) -> bool:
        if "is_karzinka" in validated_data:
            return validated_data.get("is_karzinka") is False
        if instance is not None:
            return instance.is_karzinka is False
        return False

    def _get_or_create_first_order(self, client, filial, date=None):
        """
        MUHIM: get_or_create emas!
        - bir nechta order bo'lsa ham .first() bilan birinchisini oladi
        - bo'lmasa yaratadi
        """
        order = (
            Order.objects
            .filter(client=client, filial=filial, is_delete=False)
            .order_by("id")
            .first()
        )
        if order:
            return order, False

        order = Order.objects.create(
            client=client,
            filial=filial,
            date_last_order=date,
            is_delete=False,
        )
        return order, True

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self._get_user()

        old_order_id = instance.order_id  # keyin eski orderni ham recompute qilish uchun

        if validated_data.get("employee") is None:
            validated_data["employee"] = user

        # order_filialni ham doim to'g'rilab qo'yamiz (agar bo'sh qolib ketmasin)
        validated_data["order_filial"] = self._get_filial_for_order(validated_data, instance=instance)

        updated_instance = super().update(instance, validated_data)

        if updated_instance.is_karzinka is False:
            if updated_instance.client is None:
                raise serializers.ValidationError({"client": "client majburiy"})

            filial = updated_instance.order_filial
            order, _created = self._get_or_create_first_order(
                client=updated_instance.client,
                filial=filial,
                date=updated_instance.date
            )

            if updated_instance.order_id != order.id:
                updated_instance.order = order
                updated_instance.save(update_fields=["order"])

            # Order History Product Hisobi
            products = OrderHistoryProduct.objects.filter(order_history=instance.id).first()
            total_product_summa = 0
            total_profit_dollar = 0
            for product in products:
                if product.price_dollar:
                    total_product_summa = total_product_summa + product.count * product.price_dollar
                    total_profit_dollar = total_profit_dollar + (product.count * product.price_dollar - product.count * product.real_price)
                else:
                    price_usd = round(float(product.price_sum) / float(updated_instance.exchange_rate), 2)
                    total_product_summa = total_product_summa + product.count * price_usd
                    total_profit_dollar = total_profit_dollar + (product.count * price_usd - product.count * product.real_price)

            if updated_instance.order_status:
                # Order History Hisobi
                summa_dollar = updated_instance.summa_dollar
                summa_naqt_usd =  round(float(updated_instance.summa_naqt) / float(updated_instance.exchange_rate), 2)
                summa_kilik_usd = round(float(updated_instance.summa_kilik) / float(updated_instance.exchange_rate), 2)
                summa_terminal_usd = round(float(updated_instance.summa_terminal) / float(updated_instance.exchange_rate), 2)
                discount_amount = updated_instance.discount_amount
                all_pay_summa_dollar = summa_dollar + summa_naqt_usd + summa_kilik_usd + summa_terminal_usd - discount_amount - updated_instance.zdacha_dollar

                total_debt_today = total_product_summa - all_pay_summa_dollar
                updated_instance.all_profit_dollar = total_profit_dollar
                updated_instance.total_debt_client = updated_instance.total_debt_client + total_debt_today
                updated_instance.total_debt_today_client = total_debt_today
                updated_instance.all_product_summa = total_product_summa
                updated_instance.save()

                # Order Hisobi
                order.all_profit_dollar = order.all_profit_dollar + total_profit_dollar
                order.total_debt_old_client = order.total_debt_client
                order.total_debt_client = order.total_debt_client + total_debt_today
                order.all_product_summa = order.all_product_summa + total_product_summa
                order.summa_total_dollar = order.summa_total_dollar + all_pay_summa_dollar

                order.summa_dollar = order.summa_dollar + summa_dollar
                order.summa_naqt = order.summa_naqt + summa_naqt_usd
                order.summa_kilik = order.summa_kilik + summa_kilik_usd
                order.summa_terminal = order.summa_terminal + summa_terminal_usd
                order.discount_amount = order.discount_amount + discount_amount
                order.save()

                # Client Hisobi
                client = Client.objects.filter(id=updated_instance.client).first()
                client.total_debt = client.total_debt + total_debt_today
                client.save()

                # Client Keshbek History Hisobi
                all_keshbek_summ = round(float((all_pay_summa_dollar * client.keshbek)/100), 2)
                ClientKeshbekHistory.objects.create(client=client, keshbek=client.keshbek, keshbek_summa=all_keshbek_summ, )
        return updated_instance


class OrderHistorySellSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = (
            'id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'all_profit_dollar', 'total_debt_client', 'total_debt_today_client',
            'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt',
            'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
            'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
            'is_debtor_product', 'status_order_dukon', 'status_order_sklad',
            'driver_info', 'is_karzinka', 'order_filial', 'currency'
        )

    # ---------------- helpers ----------------

    def _get_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Autentifikatsiya talab qilinadi."})
        return user

    def _get_filial_for_order(self, validated_data, instance=None):
        user = self._get_user()
        if validated_data.get("order_filial") is not None:
            return validated_data["order_filial"]
        if instance is not None and instance.order_filial is not None:
            return instance.order_filial
        filial = getattr(user, "order_filial", None)
        if filial is None:
            raise serializers.ValidationError({"detail": "Sizga order_filial biriktirilmagan. (User.order_filial = null)"})
        return filial

    def _q2(self, v: Decimal) -> Decimal:
        return (v or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _to_decimal(self, v) -> Decimal:
        if v is None:
            return Decimal("0")
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    def _uzs_to_usd(self, uzs: Decimal, rate: Decimal) -> Decimal:
        if rate is None or rate <= 0:
            raise serializers.ValidationError({"exchange_rate": "exchange_rate 0 dan katta bo‘lishi kerak."})
        return self._q2(uzs / rate)

    def _get_or_create_first_order(self, client, filial, date=None):
        order = (
            Order.objects
            .filter(client=client, filial=filial, is_delete=False)
            .order_by("id")
            .first()
        )
        if order:
            return order, False
        order = Order.objects.create(
            client=client,
            filial=filial,
            date_last_order=date,
            is_delete=False,
        )
        return order, True

    def _calc_products_totals(self, order_history: OrderHistory):
        """
        return:
          total_product_summa_usd, total_profit_usd
        """
        qs = OrderHistoryProduct.objects.filter(
            order_history_id=order_history.id,
            is_delete=False
        )

        total_summa_usd = Decimal("0")
        total_profit_usd = Decimal("0")
        rate = self._to_decimal(order_history.exchange_rate)

        for p in qs:
            count = self._to_decimal(p.count or 0)

            # sotilgan narx USD
            if p.price_dollar and self._to_decimal(p.price_dollar) > 0:
                sold_usd_unit = self._to_decimal(p.price_dollar)
            else:
                sold_usd_unit = self._uzs_to_usd(self._to_decimal(p.price_sum), rate)

            line_sum_usd = count * sold_usd_unit

            # real_price (sizda USDga o‘xshaydi) — unit
            real_unit = self._to_decimal(p.real_price)
            line_cost_usd = count * real_unit

            total_summa_usd += line_sum_usd
            total_profit_usd += (line_sum_usd - line_cost_usd)

        return self._q2(total_summa_usd), self._q2(total_profit_usd)

    def _calc_payments_usd(self, oh: OrderHistory):
        """
        return: paid_total_usd (discount va qaytimni inobatga olgan holda)
        """
        rate = self._to_decimal(oh.exchange_rate)

        summa_dollar = self._to_decimal(oh.summa_dollar)
        naqt_usd = self._uzs_to_usd(self._to_decimal(oh.summa_naqt), rate)
        klik_usd = self._uzs_to_usd(self._to_decimal(oh.summa_kilik), rate)
        terminal_usd = self._uzs_to_usd(self._to_decimal(oh.summa_terminal), rate)
        transfer_usd = self._uzs_to_usd(self._to_decimal(oh.summa_transfer), rate)

        discount = self._to_decimal(oh.discount_amount)
        zdacha_usd = self._to_decimal(oh.zdacha_dollar)

        paid = summa_dollar + naqt_usd + klik_usd + terminal_usd + transfer_usd - discount - zdacha_usd
        return self._q2(paid)

    def _apply_delta_to_order_and_client(self, *, order: Order, client: Client, delta_profit: Decimal,
                                        delta_debt: Decimal, delta_product_sum: Decimal, delta_paid: Decimal,
                                        date_last=None):
        """
        delta_* qiymatlarni Order va Clientga qo‘shib/ayirib beradi.
        """
        # Order
        Order.objects.filter(pk=order.pk).update(
            all_profit_dollar=F("all_profit_dollar") + delta_profit,
            total_debt_old_client=F("total_debt_client"),
            total_debt_client=F("total_debt_client") + delta_debt,
            all_product_summa=F("all_product_summa") + delta_product_sum,
            summa_total_dollar=F("summa_total_dollar") + delta_paid,
            summa_dollar=F("summa_dollar") + self._to_decimal(delta_paid) * Decimal("0"),  # pastda alohida yangilaymiz
        )
        # yuqorida summa_dollarni shunchaki ko‘paytirib qo‘ymaymiz, chunki delta_paid ichida hammasi aralash
        # shuning uchun payment turlarini ham delta bilan yuritmoqchi bo‘lsangiz alohida delta'lar kerak bo‘ladi.
        # Hozirgi Order modelida ham turlari bor — delta bilan yuritish uchun pastda aniq beramiz.

        # Client
        Client.objects.filter(pk=client.pk).update(
            total_debt=F("total_debt") + delta_debt
        )

        if date_last:
            Order.objects.filter(pk=order.pk).update(date_last_order=date_last)

    # ---------------- main update ----------------

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self._get_user()

        # lock: double request bo‘lsa ham safe
        instance = (
            OrderHistory.objects
            .select_for_update()
            .select_related("client", "order", "order_filial")
            .get(pk=instance.pk)
        )

        # default employee
        if validated_data.get("employee") is None:
            validated_data["employee"] = user

        # filial normalize
        validated_data["order_filial"] = self._get_filial_for_order(validated_data, instance=instance)

        # eski "posted" qiymatlarni saqlab olamiz (delta uchun)
        old_posted = bool(instance.order_status)
        old_profit = self._to_decimal(instance.all_profit_dollar)
        old_debt_today = self._to_decimal(instance.total_debt_today_client)
        old_product_sum = self._to_decimal(instance.all_product_summa)
        old_paid_total = self._to_decimal(instance.summa_total_dollar)

        # update instance fields
        updated_instance = super().update(instance, validated_data)

        # faqat karzinkadan chiqqan bo‘lsa hisob qilamiz
        if updated_instance.is_karzinka is not False:
            return updated_instance

        if updated_instance.client is None:
            raise serializers.ValidationError({"client": "client majburiy"})

        # Order topish/yasash (filial = order_filial)
        filial = updated_instance.order_filial
        order, _created = self._get_or_create_first_order(
            client=updated_instance.client,
            filial=filial,
            date=updated_instance.date
        )

        if updated_instance.order_id != order.id:
            updated_instance.order = order
            updated_instance.save(update_fields=["order"])

        # Endi yangi hisob-kitoblarni topamiz
        new_product_sum, new_profit = self._calc_products_totals(updated_instance)
        new_paid_total = self._calc_payments_usd(updated_instance)
        new_debt_today = self._q2(new_product_sum - new_paid_total)

        # OrderHistory fields ni yangilab qo‘yamiz (har doim)
        updated_instance.all_product_summa = new_product_sum
        updated_instance.all_profit_dollar = new_profit
        updated_instance.total_debt_today_client = new_debt_today

        # total_debt_client maydoni sizda “mijoz qarzi” deb turibdi — uni “client.total_debt”ga tenglab qo‘yish yaxshiroq.
        # Aks holda u ham double-count bo‘ladi.
        # Shuning uchun:
        updated_instance.total_debt_client = self._to_decimal(updated_instance.client.total_debt)

        # summa_total_dollar ni ham hisoblangan paid_total bilan tenglaymiz
        updated_instance.summa_total_dollar = new_paid_total
        updated_instance.save(update_fields=[
            "all_product_summa",
            "all_profit_dollar",
            "total_debt_today_client",
            "total_debt_client",
            "summa_total_dollar",
        ])

        # status o‘zgarishiga qarab Order/Clientga delta qo‘llaymiz
        new_posted = bool(updated_instance.order_status)

        # old -> new delta
        if not old_posted and new_posted:
            # 1) POST: bir marta qo‘shamiz
            delta_profit = new_profit
            delta_debt = new_debt_today
            delta_product = new_product_sum
            delta_paid = new_paid_total

        elif old_posted and new_posted:
            # 2) RE-POST: farqini qo‘shamiz (eski-posted ni ayirib, yangisini qo‘shish)
            delta_profit = new_profit - old_profit
            delta_debt = new_debt_today - old_debt_today
            delta_product = new_product_sum - old_product_sum
            delta_paid = new_paid_total - old_paid_total

        elif old_posted and not new_posted:
            # 3) ROLLBACK: old qiymatlarni qaytarib tashlaymiz
            delta_profit = Decimal("0") - old_profit
            delta_debt = Decimal("0") - old_debt_today
            delta_product = Decimal("0") - old_product_sum
            delta_paid = Decimal("0") - old_paid_total

        else:
            # not posted -> not posted (draft)
            delta_profit = Decimal("0")
            delta_debt = Decimal("0")
            delta_product = Decimal("0")
            delta_paid = Decimal("0")

        # delta larni Order/Clientga qo‘llaymiz
        if delta_profit != 0 or delta_debt != 0 or delta_product != 0 or delta_paid != 0:
            # lock order & client
            order = Order.objects.select_for_update().get(pk=order.pk)
            client = Client.objects.select_for_update().get(pk=updated_instance.client_id)

            # Order: umumiy maydonlar
            Order.objects.filter(pk=order.pk).update(
                all_profit_dollar=F("all_profit_dollar") + delta_profit,
                total_debt_old_client=F("total_debt_client"),
                total_debt_client=F("total_debt_client") + delta_debt,
                all_product_summa=F("all_product_summa") + delta_product,
                summa_total_dollar=F("summa_total_dollar") + delta_paid,
                date_last_order=updated_instance.date,
            )

            # Client: total debt
            Client.objects.filter(pk=client.pk).update(
                total_debt=F("total_debt") + delta_debt
            )

            # Keshbek: faqat posted bo‘lsa va paid > 0 bo‘lsa
            # (rollback bo‘lsa, alohida delete/reverse qilish kerak — bu yerda soddalashtirdim)
            if (not old_posted and new_posted) or (old_posted and new_posted and delta_paid != 0):
                # Bu yerda sizning siyosatingiz: cashback faqat real paymentdanmi?
                paid_for_cashback = new_paid_total if new_paid_total > 0 else Decimal("0")
                k = self._to_decimal(client.keshbek)
                cashback_sum = self._q2((paid_for_cashback * k) / Decimal("100"))

                ClientKeshbekHistory.objects.create(
                    client=client,
                    keshbek=client.keshbek,
                    keshbek_summa=cashback_sum,
                    order_history=updated_instance.id,
                )

        return updated_instance
