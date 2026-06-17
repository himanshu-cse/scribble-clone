from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from django.contrib.auth.models import User
from games.services import end_current_round, get_current_round, get_total_rounds, start_game, record_correct_guess
from rooms.models import Room
from .models import Game, PlayerScore, Round

def start_game_view(request, code):
    room = get_object_or_404(Room, code=code)
    game = start_game(room)
    return redirect("game_detail", game_id=game.id)

def game_detail_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    current_round = get_current_round(game)
    leaderboard = PlayerScore.objects.filter(game=game).order_by("-score")
    rounds = Round.objects.filter(game=game).order_by("round_number")

    ROUND_DURATION_SECONDS = 60
    remaining_seconds = 0
    if current_round and not current_round.ended_at:
        elapsed = (timezone.now() - current_round.started_at).total_seconds()
        remaining_seconds = max(0, ROUND_DURATION_SECONDS - int(elapsed))

    return render(
        request,
        "games/game_detail.html",
        {
            "game": game,
            "current_round": current_round,
            "total_rounds": get_total_rounds(game),
            "leaderboard": leaderboard,
            "rounds": rounds,
            "remaining_seconds": remaining_seconds,
        }
    )

def end_round_view(request, game_id):
    game = Game.objects.get(id=game_id)
    end_current_round(game)

    return redirect("game_detail", game_id=game.id)

def test_guess_view(request, game_id):
    game = Game.objects.get(id=game_id)
    current_round = get_current_round(game)
    guesser = PlayerScore.objects.filter(game=game).exclude(player=current_round.drawer).first().player

    record_correct_guess(current_round, guesser)
    return redirect("game_detail", game_id=game.id)