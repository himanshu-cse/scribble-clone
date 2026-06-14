from rooms.models import RoomPlayer
from .models import Game, PlayerScore, Round, UsedWord, Word

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
    Round.objects.create(game=game, drawer=drawer, word=word, round_number=game.current_round)

def end_round(game):
    game.current_round += 1
    game.save()

    if game.current_round > get_total_rounds(game):
        game.status = Game.FINISHED
        game.save()
        return None
    
    return start_round(game)

def get_total_rounds(game):
    player_count = RoomPlayer.objects.filter(room=game.room, is_spectator=False).count()
    return player_count * game.max_rounds

