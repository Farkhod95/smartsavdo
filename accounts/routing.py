from django.urls import path
from .consumers import WSConsumer

websocket_urlpatterns = [
    path('ws/notes/notifications/', WSConsumer.as_asgi()),
]