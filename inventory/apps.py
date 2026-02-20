from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        # signals papkasini yuklaydi (ichidagi receiverlar registratsiya bo'ladi)
        from . import signals  # noqa: F401