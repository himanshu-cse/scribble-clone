from django.shortcuts import render, redirect, get_object_or_404

from games.services import end_round, get_total_rounds, start_game
from rooms.models import Room
from .models import Game, Round

def start_game_view(request, code):
    room = get_object_or_404(Room, code=code)
    game = start_game(room)
    return redirect("game_detail", game_id=game.id)

def game_detail_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    current_round = Round.objects.filter(game=game).order_by("-round_number").first()
    return render(
        request,
        "games/game_detail.html",
        {
            "game": game,
            "current_round": current_round,
            "total_rounds": get_total_rounds(game)
        }
    )

def next_round_view(request, game_id):
    game = Game.objects.get(id=game_id)
    round_obj = end_round(game)

    return redirect("game_detail", game_id=game.id)