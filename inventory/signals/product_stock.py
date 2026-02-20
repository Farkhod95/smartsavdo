from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from inventory.models import ProductStock


@receiver(post_save, sender=ProductStock)
def productstock_post_save(sender, instance: ProductStock, **kwargs):
    if instance.product_id:
        instance.product.recalc_count_from_stocks(save=True)


@receiver(post_delete, sender=ProductStock)
def productstock_post_delete(sender, instance: ProductStock, **kwargs):
    if instance.product_id:
        instance.product.recalc_count_from_stocks(save=True)