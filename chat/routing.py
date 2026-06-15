from django.urls import re_path

from .consumers import ChatConsumer

print("CHAT ROUTING LOADED")

websocket_urlpatterns = [
    re_path(r"^ws/chat/(?P<room_code>\w+)/$", ChatConsumer.as_asgi(),),
]