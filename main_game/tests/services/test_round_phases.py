from unittest.mock import patch

from django.test import TestCase

from main_game.models import Colony, StoryText
from main_game.services.combat import CombatService
from main_game.services.research import ResearchService
from main_game.services.round_resolution import RoundService
from main_game.tests.factories import ColonyFactory, GameFactory


class RoundPhaseOrderTests(TestCase):
    def test_round_executes_phases_in_documented_order(self):
        game = GameFactory()
        colony = ColonyFactory(game=game)
        colony.ready = True
        colony.save(update_fields=["ready"])
        calls = []

        def phase(name):
            def record(instance, *args, **kwargs):
                calls.append(name)

            return record

        with (
            patch.object(Colony, "reset_fertility", autospec=True, side_effect=phase("fertility")),
            patch.object(Colony, "gather_phase", autospec=True, side_effect=phase("gather")),
            patch.object(Colony, "grow_torbs", autospec=True, side_effect=phase("growth")),
            patch.object(Colony, "call_breed_torbs", autospec=True, side_effect=phase("breeding")),
            patch.object(Colony, "rest_torbs", autospec=True, side_effect=phase("rest")),
            patch.object(
                CombatService,
                "resolve_round",
                side_effect=lambda *args, **kwargs: calls.append("combat"),
            ),
            patch.object(
                ResearchService,
                "conduct_research",
                side_effect=lambda *args, **kwargs: calls.append("research"),
            ),
            patch.object(Colony, "colony_meal", autospec=True, side_effect=phase("meal")),
        ):
            self.assertTrue(RoundService.advance_if_ready(game.pk, seed=1))

        self.assertEqual(
            calls,
            ["fertility", "gather", "growth", "breeding", "rest", "combat", "research", "meal"],
        )

    def test_failed_late_phase_rolls_back_earlier_state_and_stories(self):
        game = GameFactory()
        colony = ColonyFactory(game=game, food=5)
        colony.ready = True
        colony.save(update_fields=["ready"])
        story_count = StoryText.objects.count()

        def fail_after_writes(instance, *args, **kwargs):
            instance.food = 99
            instance.save(update_fields=["food"])
            StoryText.objects.create(
                colony=instance,
                story_text_type="system",
                story_text="must roll back",
            )
            raise RuntimeError("late phase failed")

        with patch.object(Colony, "new_round", autospec=True, side_effect=fail_after_writes):
            with self.assertRaises(RuntimeError):
                RoundService.advance_if_ready(game.pk, seed=2)

        game.refresh_from_db()
        colony.refresh_from_db()
        self.assertEqual(game.round_number, 1)
        self.assertEqual(game.round_status, game.RoundStatus.OPEN)
        self.assertEqual(colony.food, 5)
        self.assertTrue(colony.ready)
        self.assertEqual(StoryText.objects.count(), story_count)
