from django.db import transaction

from main_game.models import EvolutionEngine, Game


class GameService:
    @staticmethod
    @transaction.atomic
    def create_game(**game_data):
        game = Game.objects.create(**game_data)
        EvolutionEngine.objects.create(game=game)
        return game
