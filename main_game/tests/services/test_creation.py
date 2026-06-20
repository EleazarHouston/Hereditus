import random
from unittest.mock import patch

from django.test import TestCase

from main_game.models import Army, Colony, EvolutionEngine, Game, Lab, StoryText
from main_game.services.colony_creation import ColonyService
from main_game.services.game_creation import GameService
from main_game.tests.factories import GameFactory, PlayerFactory, UserFactory


class CreationAtomicityTests(TestCase):
    def test_game_creation_rolls_back_if_engine_creation_fails(self):
        count = Game.objects.count()
        with patch.object(EvolutionEngine.objects, "create", side_effect=RuntimeError("engine")):
            with self.assertRaises(RuntimeError):
                GameService.create_game(description="Rollback game")
        self.assertEqual(Game.objects.count(), count)

    def test_colony_creation_rolls_back_all_related_rows_on_failure(self):
        game = GameFactory(starting_torbs=2)
        player = PlayerFactory()
        counts = {
            "colonies": Colony.objects.count(),
            "armies": Army.objects.count(),
            "labs": Lab.objects.count(),
            "stories": StoryText.objects.count(),
        }

        with patch.object(Lab.objects, "create", side_effect=RuntimeError("lab")):
            with self.assertRaises(RuntimeError):
                ColonyService.create_colony(
                    game=game,
                    player=player,
                    name="Rollback colony",
                    rng=random.Random(0),
                )

        self.assertEqual(Colony.objects.count(), counts["colonies"])
        self.assertEqual(Army.objects.count(), counts["armies"])
        self.assertEqual(Lab.objects.count(), counts["labs"])
        self.assertEqual(StoryText.objects.count(), counts["stories"])

    def test_join_rejects_closed_game_and_population_cap_without_changes(self):
        user = UserFactory()
        closed = GameFactory(closed=True)
        with self.assertRaises(PermissionError):
            ColonyService.join_game(game_id=closed.pk, user=user, name="Closed")
        self.assertFalse(closed.colony_set.exists())

        open_game = GameFactory(max_colonies_per_player=1)
        first = ColonyService.join_game(game_id=open_game.pk, user=user, name="First")
        counts = (Colony.objects.count(), StoryText.objects.count())
        with self.assertRaises(ValueError):
            ColonyService.join_game(game_id=open_game.pk, user=user, name="Second")
        self.assertEqual(Colony.objects.count(), counts[0])
        self.assertEqual(StoryText.objects.count(), counts[1])
        self.assertEqual(open_game.colony_set.get(), first)
