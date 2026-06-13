import uuid

from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):

    LOBBY = "LOBBY"
    IN_GAME = "IN_GAME"

    STATUS_CHOICES = [(LOBBY, "Lobby"), (IN_GAME, "In Game"),]

    code = models.CharField(max_length=8, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=LOBBY)

    def __str__(self):
        return self.code
    
    class Meta:
        db_table = "room"
    
    
class RoomPlayer(models.Model):

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_spectator = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room", "user")
        db_table = "room_player"