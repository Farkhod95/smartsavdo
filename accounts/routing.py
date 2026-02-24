from django.urls import path
from .consumers import WSConsumer

websocket_urlpatterns = [
    path('api/v1/ws/notes/notifications/', WSConsumer.as_asgi()),
]