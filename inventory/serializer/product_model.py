from django.db.models import Max
from rest_framework import serializers

from inventory.models import ProductModel
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_branch_category import ProductBranchCategorySerializer


class ProductModelForSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch', 'branch_category', 'sorting', 'is_delete')


class ProductModelListSerializer(serializers.ModelSerializer):
    branch_detail = ProductBranchListSerializer(source='branch', read_only=True)
    branch_category_detail = ProductBranchCategorySerializer(source='branch_category', read_only=True)
    # ✅ ProductBranch (name) ni ham chiqaramiz
    # product_branch = serializers.IntegerField(source='branch_category.product_branch_id', read_only=True)
    # branch_name = serializers.CharField(source='branch_category.product_branch.name', read_only=True)

    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch', 'branch_detail',  'branch_category', 'branch_category_detail', 'sorting', 'is_delete')


class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'branch', 'branch_category', 'sorting', 'is_delete')

    def _suggest_next_sorting(self, branch_id: int, branch_category_id: int) -> int:
        max_sorting = (
            ProductModel.objects
            .filter(
                branch_id=branch_id,
                branch_category_id=branch_category_id,
                sorting__isnull=False,
                is_delete=False
            )
            .aggregate(m=Max('sorting'))
            .get('m')
        )
        return (max_sorting or 0) + 1

    def validate(self, attrs):
        branch = attrs.get('branch', getattr(self.instance, 'branch', None))
        branch_category = attrs.get('branch_category', getattr(self.instance, 'branch_category', None))
        sorting = attrs.get('sorting', getattr(self.instance, 'sorting', None))
        is_delete = attrs.get('is_delete', getattr(self.instance, 'is_delete', False))

        # sorting NULL bo'lsa tekshirmaymiz
        if branch is None or sorting is None:
            return attrs

        if branch_category is None or sorting is None:
            return attrs

        # o'chirilayotgan bo'lsa (soft delete) tekshirmaymiz
        if is_delete is True:
            return attrs

        qs = ProductModel.objects.filter(
            branch=branch,
            branch_category=branch_category,
            sorting=sorting,
            is_delete=False
        )

        # update paytida o'zini chiqaramiz
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            suggestion = self._suggest_next_sorting(branch_id=branch.id, branch_category_id=branch_category.id)
            raise serializers.ValidationError({
                "sorting": f"Bu tartib raqam band. Bo‘sh tartib raqam: {suggestion}"
            })

        return attrs