from django.db.models import Sum
from rest_framework import serializers

from inventory.models import ProductModel, ProductBranch, ProductBranchCategory
from inventory.serializer.product_model import ProductModelListSerializer
from inventory.serializer.product_branch import ProductBranchListSerializer
from inventory.serializer.product_branch_category import ProductBranchCategoryForSerializer


class OrderHistoryProductByModelGroupSerializer(serializers.Serializer):
    """
    DB'dan values()+annotate() orqali keladigan bitta group row ni chiroyli format qiladi.
    """
    model = serializers.IntegerField(allow_null=True)
    branch = serializers.IntegerField(allow_null=True)
    branch_category = serializers.IntegerField(allow_null=True)

    total_count = serializers.IntegerField()
    total_given_count = serializers.IntegerField()
    total_price_sum = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_price_dollar = serializers.DecimalField(max_digits=20, decimal_places=2)

    type_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    size_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    product_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    # detail larni contextdan qo‘shamiz
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        model_id = rep.get("model")
        branch_id = rep.get("branch")
        branch_category_id = rep.get("branch_category")

        models_map = self.context.get("models_map", {})
        branch_map = self.context.get("branch_map", {})
        branch_category_map = self.context.get("branch_category_map", {})

        model_obj = models_map.get(model_id)
        branch_obj = branch_map.get(branch_id)
        bc_obj = branch_category_map.get(branch_category_id)

        rep["model_detail"] = ProductModelListSerializer(model_obj).data if model_obj else None
        rep["branch_detail"] = ProductBranchListSerializer(branch_obj).data if branch_obj else None
        rep["branch_category_detail"] = ProductBranchCategoryForSerializer(bc_obj).data if bc_obj else None

        # null bo‘lsa []
        rep["type_ids"] = rep.get("type_ids") or []
        rep["size_ids"] = rep.get("size_ids") or []
        rep["product_ids"] = rep.get("product_ids") or []

        return rep
