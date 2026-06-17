from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Room, RoomPlayer
from .utils import generate_room_code

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@login_required
def create_room_view(request):
    room = Room.objects.create(code=generate_room_code(), owner=request.user)
    RoomPlayer.objects.create(room=room, user=request.user)
    return redirect("room_lobby", code=room.code)

@login_required
def room_lobby_view(request, code):
    room = get_object_or_404(Room, code=code)
    players = RoomPlayer.objects.filter(room=room).select_related("user")

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"room_{room.code}",
        {
            "type": "system_message",
            "command": "reload_page",
        }
    )

    return render(request, "rooms/lobby.html", {"room": room, "players": players})

@login_required
def join_room_view(request):
    if request.method == "POST":
        code = request.POST["code"].upper()
        room = Room.objects.filter(code=code).first()
        if room is None:
            return render(request, "rooms/join_room.html", {"error": "Room not found"})
        RoomPlayer.objects.get_or_create(room=room, user=request.user)
        return redirect("room_lobby", code=room.code)
    
    return render(request, "rooms/join_room.html")