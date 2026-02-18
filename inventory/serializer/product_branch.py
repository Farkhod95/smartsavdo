from rest_framework import serializers

from inventory.models import  ProductBranch


class ProductBranchForSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranch
        fields = ('id', 'name', 'sorting', 'is_delete')


class ProductBranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranch
        fields = ('id', 'name', 'sorting', 'is_delete')


class ProductBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranch
        fields = ('id', 'name', 'sorting', 'is_delete')

    def _suggest_free_sorting(self) -> int:
        """
        Bo'sh sorting raqamini topib beradi:
        - 1 dan boshlab eng kichik bo'sh raqamni qaytaradi
        - agar hammasi ketma-ket bo'lsa => max+1
        """
        used = (ProductBranch.objects
                .filter(is_delete=False, sorting__isnull=False)
                .values_list('sorting', flat=True)
                .order_by('sorting'))

        # used QuerySet bo'lgani uchun iteratsiya qilib ketamiz
        expected = 1
        for s in used:
            if s < expected:
                continue
            if s == expected:
                expected += 1
                continue
            # s > expected => expected bo'sh
            return expected

        return expected  # hammasi ketma-ket bo'lsa max+1 bo'ladi

    def validate_sorting(self, value):
        """
        sorting unique bo'lishi kerak (is_delete=False ichida).
        Band bo'lsa: qaysi branch band qilgani + tavsiya bo'sh raqamni chiqaramiz.
        """
        if value is None:
            return value

        instance = getattr(self, 'instance', None)

        qs = ProductBranch.objects.filter(is_delete=False, sorting=value)
        if instance is not None and instance.pk:
            qs = qs.exclude(pk=instance.pk)

        conflict = qs.only('id', 'name').first()
        if conflict:
            suggestion = self._suggest_free_sorting()
            conflict_name = conflict.name or f"#{conflict.id}"
            raise serializers.ValidationError(
                # (f'Bu tartib raqam band (ID={conflict.id}, Nomi="{conflict_name}"). '
                #   f'Tavsiya etiladigan bo‘sh tartib raqam: {suggestion}')
                (f'Bu tartib raqam band. '
                 f'Bo‘sh tartib raqam: {suggestion}')
            )

        return value
