import random
import secrets

from django.db import transaction

from main_game.models import Colony, Game


class RoundService:
    @classmethod
    @transaction.atomic
    def ready_colony(cls, colony_id, *, seed=None):
        game_id = Colony.objects.values_list("game_id", flat=True).get(pk=colony_id)
        game = Game.objects.select_for_update().get(pk=game_id)
        colony = Colony.objects.select_for_update().get(pk=colony_id, game=game)
        if not colony.ready:
            colony.ready = True
            colony.save(update_fields=["ready"])
        return cls._advance_locked(game, seed=seed)

    @classmethod
    @transaction.atomic
    def advance_if_ready(cls, game_id, *, seed=None):
        game = Game.objects.select_for_update().get(pk=game_id)
        return cls._advance_locked(game, seed=seed)

    @staticmethod
    def _advance_locked(game, *, seed=None):
        if game.round_status != Game.RoundStatus.OPEN:
            return False
        colonies = list(game.colony_set.select_related("player").all())
        if not colonies or any(not colony.ready for colony in colonies):
            return False

        game.round_status = Game.RoundStatus.RESOLVING
        game.round_seed = seed if seed is not None else secrets.randbits(63)
        game.save(update_fields=["round_status", "round_seed"])
        rng = random.Random(game.round_seed)
        rng.shuffle(colonies)

        for colony in colonies:
            colony.new_round(round_number=game.round_number, rng=rng)

        game.colony_set.update(ready=False)
        game.round_number += 1

        from main_game.services.ai import AIService

        for colony in colonies:
            if colony.player.user_id is None:
                AIService.make_decisions(colony, rng=rng)

        game.round_status = Game.RoundStatus.OPEN
        game.save(update_fields=["round_number", "round_status", "round_seed"])
        return True
