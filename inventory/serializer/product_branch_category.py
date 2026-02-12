from rest_framework import serializers

from inventory.models import ProductBranchCategory
from django.db.models import Max

from inventory.serializer.product_branch import ProductBranchListSerializer


class ProductBranchCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBranchCategory
        fields = ('id', 'product_branch', 'name', 'sorting', 'is_delete')
        extra_kwargs = {
            'name': {"required": False, "allow_blank": True, "allow_null": True},
            'sorting': {"required": False, "allow_null": True},
            'is_delete': {"required": False},
        }

    def _suggest_next_sorting(self, product_branch_id: int) -> int:
        """
        Shu branch ichidagi eng katta sorting + 1 ni qaytaradi.
        (sorting NULL bo'lganlar e'tiborga olinmaydi)
        """
        max_sorting = (
            ProductBranchCategory.objects
            .filter(product_branch_id=product_branch_id, sorting__isnull=False, is_delete=False)
            .aggregate(m=Max('sorting'))
            .get('m')
        )
        return (max_sorting or 0) + 1

    def validate(self, attrs):
        """
        product_branch + sorting unique:
        - sorting None bo'lsa tekshirmaymiz (ruxsat)
        - is_delete=True bo'lsa tekshirmaymiz (xohlasangiz tekshiradigan qilib ham qo'yish mumkin)
        - update(paytida) o'zini exclude qilamiz
        """
        # Update paytida attrs kelmasligi mumkin, shuning uchun instance dan olamiz
        product_branch = attrs.get('product_branch', getattr(self.instance, 'product_branch', None))
        sorting = attrs.get('sorting', getattr(self.instance, 'sorting', None))
        is_delete = attrs.get('is_delete', getattr(self.instance, 'is_delete', False))

        # kerakli holatlar
        if product_branch is None or sorting is None:
            return attrs  # sorting null bo'lsa unique tekshiruv yo'q
        if is_delete is True:
            return attrs  # o'chirilayotgan bo'lsa xohlasangiz tekshirmaslik

        qs = ProductBranchCategory.objects.filter(
            product_branch=product_branch,
            sorting=sorting,
            is_delete=False,
        )

        # Update bo'lsa o'zini chiqarib tashlaymiz
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            suggestion = self._suggest_next_sorting(product_branch_id=product_branch.id)
            raise serializers.ValidationError({
                'sorting': f'Bu tartib raqam band. Bo‘sh tartib raqam: {suggestion}'
            })

        return attrs


class ProductBranchCategoryListSerializer(serializers.ModelSerializer):
    product_branch_detail = ProductBranchListSerializer(source='product_branch', read_only=True)

    class Meta:
        model = ProductBranchCategory
        fields = ('id', 'product_branch', 'product_branch_detail', 'name', 'sorting', 'is_delete')
