from django.db import models
from rooms.models import Room
from django.contrib.auth.models import User

from django.db.models import Q

class Word(models.Model):
    text = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.text
    
class Game(models.Model):
    LOBBY = "LOBBY"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"

    STATUS_CHOICES = [(LOBBY, "Lobby"), (IN_PROGRESS, "In Progress"), (FINISHED, "Finished")]

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=LOBBY)
    current_round = models.IntegerField(default=0)
    max_rounds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["room"],
                condition=Q(status="IN_PROGRESS"),
                name="one_active_game_per_room",
            )
        ]

class Round(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    drawer = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    round_number = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class PlayerScore(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ("game", "player")

class UsedWord(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)

class RoundGuess(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    guessed_correctly = models.BooleanField(default=True)
    guessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("round", "player")
