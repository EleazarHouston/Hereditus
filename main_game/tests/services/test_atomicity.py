from unittest.mock import patch

from django.test import TestCase

from main_game.models import StoryText, Torb
from main_game.services.actions import ActionService
from main_game.services.combat import CombatService
from main_game.services.research import ResearchService
from main_game.tests.factories import ColonyFactory, TorbFactory


class FailedActionAtomicityTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.player = self.colony.player

    def test_partial_breeding_assignment_rolls_back(self):
        first = TorbFactory(colony=self.colony, private_ID=1)
        second = TorbFactory(colony=self.colony, private_ID=2)
        original = Torb.set_action
        call_count = 0

        def fail_second(instance, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("second assignment failed")
            return original(instance, *args, **kwargs)

        with patch.object(Torb, "set_action", autospec=True, side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                ActionService.perform(
                    player=self.player,
                    colony=self.colony,
                    action="breed",
                    torb_ids=[first.pk, second.pk],
                )

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.action, Torb.Action.GATHERING)
        self.assertEqual(second.action, Torb.Action.GATHERING)
        self.assertIsNone(first.context_torb)
        self.assertIsNone(second.context_torb)

    def test_research_write_and_story_roll_back_together(self):
        self.colony.lab.science_points = 20
        self.colony.lab.save(update_fields=["science_points"])
        story_count = StoryText.objects.count()

        def mutate_then_fail(lab, amount):
            lab.science_points -= 10
            lab.save(update_fields=["science_points"])
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="science",
                story_text="must roll back",
            )
            raise RuntimeError("conversion failed")

        with patch.object(ResearchService, "make_mutagen", side_effect=mutate_then_fail):
            with self.assertRaises(RuntimeError):
                ActionService.perform(
                    player=self.player,
                    colony=self.colony,
                    action="make_mutagen",
                    science_points_used=10,
                )

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 20)
        self.assertEqual(StoryText.objects.count(), story_count)

    def test_combat_target_and_story_roll_back_together(self):
        target = ColonyFactory(game=self.colony.game, name="Target")
        story_count = StoryText.objects.count()

        def mutate_then_fail(*, colony, action, target_id):
            colony.army.scout_target_id = target_id
            colony.army.save(update_fields=["scout_target"])
            StoryText.objects.create(
                colony=colony,
                story_text_type="scout",
                story_text="must roll back",
            )
            raise RuntimeError("targeting failed")

        with patch.object(CombatService, "set_target", side_effect=mutate_then_fail):
            with self.assertRaises(RuntimeError):
                ActionService.perform(
                    player=self.player,
                    colony=self.colony,
                    action="scout",
                    target_colony_id=target.pk,
                )

        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.scout_target)
        self.assertEqual(StoryText.objects.count(), story_count)

    def test_successful_action_commits_state_and_story(self):
        self.colony.lab.science_points = 10
        self.colony.lab.save(update_fields=["science_points"])
        story_count = StoryText.objects.count()

        ActionService.perform(
            player=self.player,
            colony=self.colony,
            action="make_mutagen",
            science_points_used=10,
        )

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 0)
        self.assertEqual(self.colony.lab.mutagen, 1)
        self.assertEqual(StoryText.objects.count(), story_count + 1)
