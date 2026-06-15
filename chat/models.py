from django.db import models

from rooms.models import Room
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)