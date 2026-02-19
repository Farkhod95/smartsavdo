from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from accounts.serializers import FilialListSerializer
from finance.models import DebtRepayment
from sales.models import Client  # sizda qayerda bo‘lsa moslang
from sales.serializer.client import ClientListSerializer
from users.serializers import UserViewListSerializer


class DebtRepaymentAccountingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtRepayment
        fields = (
            'id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note',
            'old_total_debt_client', 'total_debt_client',
            'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
            'summa_terminal', 'summa_transfer',
            'discount_amount', 'zdacha_dollar', 'zdacha_som',
            'is_delete', 'debt_status'
        )
        read_only_fields = ('old_total_debt_client', 'total_debt_client', 'summa_total_dollar')

    # -------- helpers --------

    def _q2(self, v: Decimal) -> Decimal:
        return (v or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _to_decimal(self, v) -> Decimal:
        if v is None:
            return Decimal("0")
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    def _get_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"detail": "Autentifikatsiya talab qilinadi."})
        return user

    def _uzs_to_usd(self, uzs: Decimal, rate: Decimal) -> Decimal:
        rate = self._to_decimal(rate)
        if rate <= 0:
            raise serializers.ValidationError({"exchange_rate": "exchange_rate 0 dan katta bo‘lishi kerak."})
        return self._q2(self._to_decimal(uzs) / rate)

    def _calc_paid_total_usd(self, obj: DebtRepayment) -> Decimal:
        """
        paid_total_usd = USD + (UZS payments / rate) - discount - change_usd
        """
        rate = self._to_decimal(obj.exchange_rate)

        usd = self._to_decimal(obj.summa_dollar)

        naqt_usd = self._uzs_to_usd(self._to_decimal(obj.summa_naqt), rate)
        klik_usd = self._uzs_to_usd(self._to_decimal(obj.summa_kilik), rate)
        terminal_usd = self._uzs_to_usd(self._to_decimal(obj.summa_terminal), rate)
        transfer_usd = self._uzs_to_usd(self._to_decimal(obj.summa_transfer), rate)

        discount = self._to_decimal(obj.discount_amount)
        change_usd = self._to_decimal(obj.zdacha_dollar)

        paid = usd + naqt_usd + klik_usd + terminal_usd + transfer_usd - discount - change_usd
        return self._q2(paid)

    # -------- validate --------

    def validate(self, attrs):
        client = attrs.get("client") or getattr(self.instance, "client", None)
        if not client:
            raise serializers.ValidationError({"client": "client majburiy."})

        rate = attrs.get("exchange_rate", getattr(self.instance, "exchange_rate", None))
        if rate is None:
            raise serializers.ValidationError({"exchange_rate": "exchange_rate majburiy."})
        if self._to_decimal(rate) <= 0:
            raise serializers.ValidationError({"exchange_rate": "exchange_rate 0 dan katta bo‘lishi kerak."})

        # count/amountlar manfiy bo‘lmasin
        money_fields = ["summa_dollar", "summa_naqt", "summa_kilik", "summa_terminal", "summa_transfer", "discount_amount", "zdacha_dollar"]
        for f in money_fields:
            v = attrs.get(f, getattr(self.instance, f, 0))
            if self._to_decimal(v) < 0:
                raise serializers.ValidationError({f: f"{f} manfiy bo‘lishi mumkin emas."})

        return attrs

    # -------- create/update --------

    @transaction.atomic
    def create(self, validated_data):
        user = self._get_user()

        if validated_data.get("employee") is None:
            validated_data["employee"] = user

        # client lock
        client = Client.objects.select_for_update().get(pk=validated_data["client"].id)

        # snapshot (old debt)
        validated_data["old_total_debt_client"] = self._to_decimal(client.total_debt)
        validated_data["total_debt_client"] = self._to_decimal(client.total_debt)

        # temp object to calculate paid_total
        temp = DebtRepayment(**validated_data)
        paid_total = self._calc_paid_total_usd(temp)
        validated_data["summa_total_dollar"] = paid_total

        inst = super().create(validated_data)

        # apply debt change only if confirmed
        if inst.debt_status:
            # qarzdan qancha yechildi?
            pay = paid_total if paid_total > 0 else Decimal("0")
            new_debt = self._to_decimal(client.total_debt) - pay
            if new_debt < 0:
                # xohlasangiz 0 ga tushirib qo'yish ham mumkin, lekin bu yerda xato qaytaramiz
                raise serializers.ValidationError({"summa_total_dollar": "To‘lov mijoz qarzidan katta bo‘lib ketdi."})

            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") - pay)
            inst.total_debt_client = self._to_decimal(client.total_debt) - pay
            inst.save(update_fields=["total_debt_client"])

        return inst

    @transaction.atomic
    def update(self, instance: DebtRepayment, validated_data):
        user = self._get_user()

        # lock repayment row
        instance = DebtRepayment.objects.select_for_update(of=("self",)).get(pk=instance.pk)

        # lock client
        if not instance.client_id and not validated_data.get("client"):
            raise serializers.ValidationError({"client": "client majburiy."})

        new_client = validated_data.get("client", instance.client)
        client = Client.objects.select_for_update().get(pk=new_client.id)

        if validated_data.get("employee") is None:
            validated_data["employee"] = instance.employee_id or user

        # old snapshot for delta
        old_confirmed = bool(instance.debt_status)
        old_paid_total = self._to_decimal(instance.summa_total_dollar)

        # update fields
        updated = super().update(instance, validated_data)

        # always recompute summa_total_dollar from updated fields
        new_paid_total = self._calc_paid_total_usd(updated)

        # write snapshots
        updated.old_total_debt_client = self._to_decimal(client.total_debt)  # hozirgi client debt (lock holatda)
        updated.summa_total_dollar = new_paid_total
        updated.save(update_fields=["old_total_debt_client", "summa_total_dollar"])

        new_confirmed = bool(updated.debt_status)

        # delta logic for client.total_debt
        if not old_confirmed and new_confirmed:
            # newly confirmed: subtract full new paid
            delta = new_paid_total
        elif old_confirmed and new_confirmed:
            # re-confirmed edit: subtract only difference
            delta = new_paid_total - old_paid_total
        elif old_confirmed and not new_confirmed:
            # rollback: add back old paid
            delta = Decimal("0") - old_paid_total
        else:
            delta = Decimal("0")

        # apply delta (delta >0 => debt decreases, delta<0 => debt increases back)
        if delta != 0:
            # if delta positive => debt - delta ; if delta negative => debt - (neg) => debt + abs
            new_debt = self._to_decimal(client.total_debt) - delta
            if new_debt < 0:
                raise serializers.ValidationError({"summa_total_dollar": "Natijada mijoz qarzi manfiy bo‘lib qolyapti."})

            Client.objects.filter(pk=client.pk).update(total_debt=F("total_debt") - delta)

        # updated.total_debt_client ni client’dan qayta oling (DB update dan keyin o‘qish shart emas — formula bilan)
        # client.total_debt bu yerda eski, shuning uchun hisoblab qo'yamiz:
        updated.total_debt_client = self._to_decimal(client.total_debt) - delta
        updated.save(update_fields=["total_debt_client"])

        return updated


class DebtRepaymentListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)
    employee_detail = UserViewListSerializer(source='employee', read_only=True)

    class Meta:
        model = DebtRepayment
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'employee_detail', 'exchange_rate', 'date',
                  'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar',
                  'zdacha_som', 'is_delete', 'debt_status')


class DebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtRepayment
        fields = ('id', 'filial', 'client', 'employee', 'exchange_rate', 'date', 'note', 'old_total_debt_client',
                  'total_debt_client', 'summa_total_dollar', 'summa_dollar', 'summa_naqt', 'summa_kilik',
                  'summa_terminal', 'summa_transfer', 'discount_amount', 'zdacha_dollar', 'zdacha_som',
                  'is_delete', 'debt_status')


