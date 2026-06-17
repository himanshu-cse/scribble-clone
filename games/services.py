from rooms.models import RoomPlayer
from .models import Game, PlayerScore, Round, UsedWord, Word, RoundGuess
from django.utils import timezone

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def get_active_game(room):
    return Game.objects.filter(room=room, status=Game.IN_PROGRESS).first()

def get_current_round(game):
    return Round.objects.filter(game=game, round_number=game.current_round).first()

def start_game(room):
    game = Game.objects.create(room=room, status=Game.IN_PROGRESS, current_round=1, max_rounds=3)
    players = RoomPlayer.objects.filter(room=room, is_spectator=False)
    
    for player in players:
        PlayerScore.objects.create(game=game, player=player.user)

    start_round(game)

    return game

def choose_drawer(game):
    players = RoomPlayer.objects.filter(room=game.room, is_spectator=False).order_by("joined_at")
    drawer_index = (game.current_round - 1) % len(players)
    return players[drawer_index].user

def choose_word(game):
    used_words_ids = UsedWord.objects.filter(game=game).values_list("word_id", flat=True)
    word = Word.objects.exclude(id__in=used_words_ids).order_by("?").first()
    UsedWord.objects.create(game=game, word=word)
    return word

def start_round(game):
    drawer = choose_drawer(game)
    word = choose_word(game)
    round_obj = Round.objects.create(game=game, drawer=drawer, word=word, round_number=game.current_round)
    return round_obj

def end_current_round(game):
    current_round = get_current_round(game)

    if not current_round or current_round.ended_at:
        return

    current_round.ended_at = timezone.now()
    current_round.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{game.room.code}",
        {
            "type": "system_message", 
            "command": "reload_page"
        }
    )

def start_next_round(game):
    game.current_round += 1

    if game.current_round > get_total_rounds(game):
        game.status = Game.FINISHED
        game.save()
    else:
        game.save()
        start_round(game)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{game.room.code}",
        {
            "type": "system_message",  
            "command": "reload_page"
        }
    )

def get_total_rounds(game):
    player_count = RoomPlayer.objects.filter(room=game.room, is_spectator=False).count()
    return player_count * game.max_rounds

def award_points(game, player, points):
    score = PlayerScore.objects.get(game=game, player=player)
    score.score += points
    score.save()
    return score

def record_correct_guess(round_obj, player):

    if player == round_obj.drawer:
        return False

    guess, created = RoundGuess.objects.get_or_create(round=round_obj, player=player)

    if not created:
        return False
    
    award_points(round_obj.game, player, 100)
    award_points(round_obj.game, round_obj.drawer, 20)

    if everyone_guessed(round_obj):
        end_current_round(round_obj.game)

    return True

def get_correct_guess_count(round_obj):
    return RoundGuess.objects.filter(round=round_obj).count()

def get_eligible_guessers(round_obj):
    return RoomPlayer.objects.filter(room=round_obj.game.room, is_spectator=False).count() - 1

def everyone_guessed(round_obj):
    return (get_correct_guess_count(round_obj) >= get_eligible_guessers(round_obj))

def process_guess(room, player, message):
    game = get_active_game(room)
    if not game:
        return False
    
    current_round = get_current_round(game)

    if not current_round or current_round.ended_at:
        return False

    if (message.lower().strip() == current_round.word.text.lower()):
        return record_correct_guess(current_round, player)
    
    return False


