from rest_framework import serializers
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import F

from accounts.serializers import FilialSerializer, CurrencySerializer

from sales.models import Order, OrderHistory, OrderHistoryProduct, Client, ClientKeshbekHistory
from sales.serializer.client import ClientSerializer, ReportClientSerializer
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
            'is_debtor_product', 'status_order_dukon', 'status_order_sklad', 'price_difference',
            'driver_info', 'is_karzinka', 'order_filial', 'currency'
        )


class OrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = ('id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note', 'all_profit_dollar',
                  'total_debt_client', 'total_debt_today_client', 'all_product_summa', 'summa_total_dollar',
                  'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
                  'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status', 'is_debtor_product',
                  'status_order_dukon', 'status_order_sklad', 'driver_info', 'is_karzinka', 'order_filial', 'currency',
                  'price_difference')


class ReportOrderHistoryListSerializer(serializers.ModelSerializer):
    client_detail = ReportClientSerializer(source='client', read_only=True)
    order_filial_detail = FilialSerializer(source='order_filial', read_only=True)
    created_by_detail = UserViewListShortSerializer(source='created_by', read_only=True)
    currency_detail = CurrencySerializer(source='currency', read_only=True)

    class Meta:
        model = OrderHistory
        fields = ('id', 'client', 'client_detail', 'employee', 'exchange_rate', 'date', 'note',
                  'all_profit_dollar', 'total_debt_client', 'total_debt_today_client', 'all_product_summa',
                  'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer',
                  'discount_amount', 'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
                  'is_debtor_product', 'status_order_dukon', 'status_order_sklad', 'driver_info', 'is_karzinka',
                  'created_time', 'created_by', 'created_by_detail', 'order_filial', 'order_filial_detail',
                  'currency', 'currency_detail', 'price_difference')


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
                  'currency', 'currency_detail', 'price_difference')


class OrderHistoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = (
            'id', 'order', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'all_profit_dollar', 'total_debt_client', 'total_debt_today_client',
            'all_product_summa', 'summa_total_dollar', 'summa_dollar', 'summa_naqt',
            'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount',
            'zdacha_dollar', 'zdacha_som', 'is_delete', 'order_status', 'update_status',
            'is_debtor_product', 'status_order_dukon', 'status_order_sklad', 'price_difference',
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
            'price_difference', 'driver_info', 'is_karzinka', 'order_filial', 'currency'
        )
        read_only_fields = (
            'all_profit_dollar',
            'total_debt_client',
            'total_debt_today_client',
            'all_product_summa',
            'summa_total_dollar',
        )

    # ---------------- helpers ----------------

    def _get_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({
                "detail": "Autentifikatsiya talab qilinadi."
            })
        return user

    def _to_decimal(self, value):
        if value is None or value == "":
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def _q2(self, value):
        return self._to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _uzs_to_usd(self, uzs, rate):
        uzs = self._to_decimal(uzs)
        rate = self._to_decimal(rate)

        if uzs == 0:
            return Decimal("0")

        if rate <= 0:
            raise serializers.ValidationError({
                "exchange_rate": "exchange_rate 0 dan katta bo‘lishi kerak."
            })

        return self._q2(uzs / rate)

    def _get_filial_for_order(self, validated_data, instance=None):
        user = self._get_user()

        if validated_data.get("order_filial") is not None:
            return validated_data["order_filial"]

        if instance is not None and instance.order_filial is not None:
            return instance.order_filial

        filial = getattr(user, "order_filial", None)
        if filial is None:
            raise serializers.ValidationError({
                "detail": "Sizga order_filial biriktirilmagan. (User.order_filial = null)"
            })
        return filial

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

    def _calc_products_totals(self, order_history):
        """
        Mahsulotlar bo'yicha:
        - total sotuv summa (USD)
        - total foyda (USD)
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

            if count <= 0:
                continue

            # sotuvdagi unit price
            if self._to_decimal(p.price_dollar) > 0:
                sold_usd_unit = self._to_decimal(p.price_dollar)
            else:
                sold_usd_unit = self._uzs_to_usd(self._to_decimal(p.price_sum), rate)

            line_sum_usd = count * sold_usd_unit
            real_unit = self._to_decimal(p.real_price)
            line_cost_usd = count * real_unit

            total_summa_usd += line_sum_usd
            total_profit_usd += (line_sum_usd - line_cost_usd)

        return self._q2(total_summa_usd), self._q2(total_profit_usd)

    def _calc_payments_usd(self, oh):
        """
        Effective payment:
        dollar
        + naqt(uzs->usd)
        + click(uzs->usd)
        + terminal(uzs->usd)
        + transfer(uzs->usd)
        + discount
        - qaytim dollar
        - qaytim som
        """
        rate = self._to_decimal(oh.exchange_rate)

        summa_dollar = self._to_decimal(oh.summa_dollar)
        naqt_usd = self._uzs_to_usd(self._to_decimal(oh.summa_naqt), rate)
        klik_usd = self._uzs_to_usd(self._to_decimal(oh.summa_kilik), rate)
        terminal_usd = self._uzs_to_usd(self._to_decimal(oh.summa_terminal), rate)
        transfer_usd = self._uzs_to_usd(self._to_decimal(oh.summa_transfer), rate)

        discount_usd = self._to_decimal(oh.discount_amount)
        zdacha_dollar = self._to_decimal(oh.zdacha_dollar)
        zdacha_som_usd = self._uzs_to_usd(self._to_decimal(oh.zdacha_som), rate)

        paid = (
            summa_dollar
            + naqt_usd
            + klik_usd
            + terminal_usd
            + transfer_usd
            + discount_usd
            - zdacha_dollar
            - zdacha_som_usd
        )
        return self._q2(paid)

    def _sync_cashback_history(self, *, client, order_history_id, paid_total_usd, is_posted):
        """
        ClientKeshbekHistory.order_history = IntegerField
        shuning uchun object emas, int yuboriladi
        """
        if not order_history_id:
            return

        if not is_posted:
            ClientKeshbekHistory.objects.filter(order_history=order_history_id).delete()
            return

        paid_total_usd = self._q2(paid_total_usd if paid_total_usd > 0 else Decimal("0"))
        keshbek_percent = self._to_decimal(client.keshbek)
        cashback_sum = self._q2((paid_total_usd * keshbek_percent) / Decimal("100"))

        ClientKeshbekHistory.objects.update_or_create(
            order_history=order_history_id,
            defaults={
                "client": client,
                "keshbek": keshbek_percent,
                "keshbek_summa": cashback_sum,
            }
        )

    def validate(self, attrs):
        exchange_rate = attrs.get("exchange_rate")
        if exchange_rate is not None and self._to_decimal(exchange_rate) < 0:
            raise serializers.ValidationError({
                "exchange_rate": "exchange_rate manfiy bo‘lishi mumkin emas."
            })
        return attrs

    # ---------------- main update ----------------

    @transaction.atomic
    def update(self, instance, validated_data):
        user = self._get_user()

        instance = OrderHistory.objects.select_for_update().get(pk=instance.pk)

        if validated_data.get("employee") is None:
            validated_data["employee"] = user

        validated_data["order_filial"] = self._get_filial_for_order(validated_data, instance=instance)

        old_posted = bool(instance.order_status)
        old_profit = self._to_decimal(instance.all_profit_dollar)
        old_debt_today = self._to_decimal(instance.total_debt_today_client)
        old_product_sum = self._to_decimal(instance.all_product_summa)
        old_paid_total = self._to_decimal(instance.summa_total_dollar)

        updated_instance = super().update(instance, validated_data)

        # faqat karzinkadan sotuvga o'tayotgan order bo'lsa ishlasin
        if updated_instance.is_karzinka:
            return updated_instance

        if updated_instance.client is None:
            raise serializers.ValidationError({
                "client": "client majburiy"
            })

        filial = updated_instance.order_filial

        order, _created = self._get_or_create_first_order(
            client=updated_instance.client,
            filial=filial,
            date=updated_instance.date
        )

        if updated_instance.order_id != order.id:
            updated_instance.order = order
            updated_instance.save(update_fields=["order"])

        # yangi hisob
        new_product_sum, new_profit = self._calc_products_totals(updated_instance)
        new_paid_total = self._calc_payments_usd(updated_instance)
        new_debt_today = self._q2(new_product_sum - new_paid_total)

        updated_instance.all_product_summa = new_product_sum
        updated_instance.all_profit_dollar = new_profit
        updated_instance.total_debt_today_client = new_debt_today
        updated_instance.summa_total_dollar = new_paid_total

        updated_instance.save(update_fields=[
            "all_product_summa",
            "all_profit_dollar",
            "total_debt_today_client",
            "summa_total_dollar",
        ])

        new_posted = bool(updated_instance.order_status)

        # delta logika
        if not old_posted and new_posted:
            delta_profit = new_profit
            delta_debt = new_debt_today
            delta_product = new_product_sum
            delta_paid = new_paid_total

        elif old_posted and new_posted:
            delta_profit = new_profit - old_profit
            delta_debt = new_debt_today - old_debt_today
            delta_product = new_product_sum - old_product_sum
            delta_paid = new_paid_total - old_paid_total

        elif old_posted and not new_posted:
            delta_profit = -old_profit
            delta_debt = -old_debt_today
            delta_product = -old_product_sum
            delta_paid = -old_paid_total

        else:
            delta_profit = Decimal("0")
            delta_debt = Decimal("0")
            delta_product = Decimal("0")
            delta_paid = Decimal("0")

        order = Order.objects.select_for_update().get(pk=order.pk)
        client = Client.objects.select_for_update().get(pk=updated_instance.client_id)

        if delta_profit != 0 or delta_debt != 0 or delta_product != 0 or delta_paid != 0:
            Order.objects.filter(pk=order.pk).update(
                all_profit_dollar=F("all_profit_dollar") + delta_profit,
                total_debt_old_client=F("total_debt_client"),
                total_debt_client=F("total_debt_client") + delta_debt,
                all_product_summa=F("all_product_summa") + delta_product,
                summa_total_dollar=F("summa_total_dollar") + delta_paid,
                date_last_order=updated_instance.date,
            )

            Client.objects.filter(pk=client.pk).update(
                total_debt=F("total_debt") + delta_debt
            )

        client.refresh_from_db(fields=["total_debt"])

        updated_instance.total_debt_client = self._to_decimal(client.total_debt)
        updated_instance.save(update_fields=["total_debt_client"])

        self._sync_cashback_history(
            client=client,
            order_history_id=updated_instance.id,
            paid_total_usd=new_paid_total,
            is_posted=new_posted
        )

        return updated_instance