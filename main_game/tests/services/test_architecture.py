from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from main_game.models import Army, Colony, EvolutionEngine, Game, Lab, StoryText
from main_game.services.actions import ActionService
from main_game.services.round_resolution import RoundService
from main_game.tests.factories import ColonyFactory, GameFactory, PlayerFactory, TorbFactory


class CreationServiceTests(TestCase):
    def test_model_saves_have_no_creation_side_effects(self):
        game = Game.objects.create(description="Pure game", starting_torbs=0)
        player = PlayerFactory()
        colony = Colony.objects.create(game=game, player=player, name="Pure colony")

        self.assertFalse(EvolutionEngine.objects.filter(game=game).exists())
        self.assertFalse(Army.objects.filter(colony=colony).exists())
        self.assertFalse(Lab.objects.filter(colony=colony).exists())
        self.assertFalse(StoryText.objects.filter(colony=colony).exists())
        self.assertFalse(colony.torbs.exists())


class ActionServiceTests(TestCase):
    def test_rejects_action_for_unowned_colony(self):
        colony = ColonyFactory()
        attacker = PlayerFactory()

        with self.assertRaises(PermissionDenied):
            ActionService.perform(player=attacker, colony=colony, action="gather", torb_ids=[])

    def test_rejects_cross_game_target(self):
        colony = ColonyFactory()
        target = ColonyFactory()

        with self.assertRaisesMessage(ValueError, "same game"):
            ActionService.perform(
                player=colony.player,
                colony=colony,
                action="scout",
                target_colony_id=target.pk,
            )
        self.assertIsNone(colony.army.scout_target)


class RoundServiceTests(TestCase):
    def test_round_advances_once_and_persists_seed(self):
        game = GameFactory()
        first = ColonyFactory(game=game, name="First")
        second = ColonyFactory(game=game, name="Second")

        self.assertFalse(RoundService.ready_colony(first.pk, seed=123))
        self.assertTrue(RoundService.ready_colony(second.pk, seed=123))
        self.assertFalse(RoundService.advance_if_ready(game.pk, seed=999))

        game.refresh_from_db()
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(game.round_number, 2)
        self.assertEqual(game.round_seed, 123)
        self.assertEqual(game.round_status, Game.RoundStatus.OPEN)
        self.assertFalse(first.ready)
        self.assertFalse(second.ready)

    def test_phase_failure_rolls_back_entire_round(self):
        game = GameFactory()
        colony = ColonyFactory(game=game)
        colony.ready = True
        colony.save(update_fields=["ready"])

        with patch.object(Colony, "new_round", side_effect=RuntimeError("phase failed")):
            with self.assertRaises(RuntimeError):
                RoundService.advance_if_ready(game.pk, seed=42)

        game.refresh_from_db()
        colony.refresh_from_db()
        self.assertEqual(game.round_number, 1)
        self.assertEqual(game.round_status, Game.RoundStatus.OPEN)
        self.assertTrue(colony.ready)

    def test_same_seed_reproduces_starvation_outcome(self):
        outcomes = []
        for game_number in range(2):
            game = GameFactory()
            colony = ColonyFactory(game=game, name=f"Seeded {game_number}", food=1)
            for private_id in range(1, 4):
                TorbFactory(colony=colony, private_ID=private_id, hp=5, max_hp=5)
            colony.ready = True
            colony.save(update_fields=["ready"])
            RoundService.advance_if_ready(game.pk, seed=2026)
            outcomes.append(list(colony.torbs.order_by("private_ID").values_list("hp", "starving")))

        self.assertEqual(outcomes[0], outcomes[1])
