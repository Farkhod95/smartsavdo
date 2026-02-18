from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from accounts.serializers import  FilialListSerializer
from sales.models import  VozvratOrder, Order, OrderHistoryProduct, Client
from sales.serializer.client import ClientListSerializer


class VozvratOrderListSerializer(serializers.ModelSerializer):
    filial_detail = FilialListSerializer(source='filial', read_only=True)
    client_detail = ClientListSerializer(source='client', read_only=True)

    class Meta:
        model = VozvratOrder
        fields = ('id', 'filial', 'filial_detail', 'client', 'client_detail', 'employee', 'exchange_rate', 'date',
                  'note', 'old_total_debt_client', 'total_debt_client', 'summa_total_dollar', 'summa_dollar',
                  'summa_naqt', 'summa_kilik', 'summa_terminal', 'summa_transfer', 'discount_amount', 'is_delete',
                  'is_vazvrat_status', 'is_karzinka')


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