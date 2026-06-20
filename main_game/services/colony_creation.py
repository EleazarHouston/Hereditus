import random

from django.db import transaction

from main_game.models import Army, Colony, Game, Lab, Player, StoryText


class ColonyService:
    @staticmethod
    @transaction.atomic
    def create_colony(*, game, player, name, rng=None, **colony_data):
        rng = rng or random.Random()
        colony = Colony.objects.create(name=name, game=game, player=player, **colony_data)
        Army.objects.create(colony=colony)
        Lab.objects.create(colony=colony)
        colony.discovered_colonies.add(colony)
        StoryText.objects.create(
            colony=colony,
            story_text_type="system",
            story_text="Welcome to Hereditus!",
        )
        for _ in range(game.starting_torbs):
            game.evolution_engine_instance.protogenesis_torb(colony=colony, rng=rng)
        return colony

    @classmethod
    @transaction.atomic
    def join_game(cls, *, game_id, user, name, rng=None):
        game = Game.objects.select_for_update().get(pk=game_id)
        if game.closed and not game.allowed_players.filter(pk=user.pk).exists():
            raise PermissionError("This game is closed.")
        player, _ = Player.objects.get_or_create(user=user, defaults={"name": user.username})
        if game.colony_set.filter(player=player).count() >= game.max_colonies_per_player:
            raise ValueError("You already have the max number of colonies for this game.")
        return cls.create_colony(game=game, player=player, name=name, rng=rng)
