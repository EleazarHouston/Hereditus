from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from main_game.models import StoryText, Torb
from main_game.services.actions import ActionService
from main_game.services.round_resolution import RoundService
from main_game.tests.factories import ColonyFactory, DiscoveryFactory, PlayerFactory, TorbFactory


class ActionValidationTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.player = self.colony.player
        self.torb = TorbFactory(colony=self.colony, private_ID=1)

    def perform(self, action, **kwargs):
        return ActionService.perform(
            player=self.player,
            colony=self.colony,
            action=action,
            **kwargs,
        )

    def test_every_torb_action_dispatches_with_valid_payload(self):
        transitions = {
            "gather": Torb.Action.GATHERING,
            "enlist": Torb.Action.TRAINING,
            "research": Torb.Action.RESEARCHING,
        }
        for action, expected in transitions.items():
            with self.subTest(action=action):
                self.torb.set_action(Torb.Action.RESTING)
                self.perform(action, torb_ids=[self.torb.pk])
                self.torb.refresh_from_db()
                self.assertEqual(self.torb.action, expected)

    def test_breed_dispatches_only_valid_pair(self):
        partner = TorbFactory(colony=self.colony, private_ID=2)

        self.perform("breed", torb_ids=[self.torb.pk, partner.pk])

        self.torb.refresh_from_db()
        partner.refresh_from_db()
        self.assertEqual(self.torb.action, Torb.Action.BREEDING)
        self.assertEqual(partner.action, Torb.Action.BREEDING)
        self.assertEqual(self.torb.context_torb, partner)

    def test_combat_actions_validate_and_set_same_game_targets(self):
        target = ColonyFactory(game=self.colony.game, name="Target")
        self.perform("scout", target_colony_id=target.pk)
        self.colony.army.refresh_from_db()
        self.assertEqual(self.colony.army.scout_target, target)

        self.colony.discovered_colonies.add(target)
        self.perform("attack", target_colony_id=target.pk)
        self.colony.army.refresh_from_db()
        self.assertEqual(self.colony.army.attack_target, target)

    def test_end_turn_dispatches_to_round_service(self):
        with patch.object(RoundService, "ready_colony", return_value=False) as ready:
            self.perform("end_turn")

        ready.assert_called_once_with(self.colony.pk)

    def test_research_purchases_validate_affordability(self):
        discovery = DiscoveryFactory(research_cost=10)
        self.colony.lab.science_points = 20
        self.colony.lab.save(update_fields=["science_points"])

        self.perform("make_mutagen", science_points_used=10)
        self.perform("purchase_discovery", discovery_id=discovery.pk)

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 0)
        self.assertEqual(self.colony.lab.mutagen, 1)
        self.assertTrue(self.colony.lab.discoveries.filter(pk=discovery.pk).exists())

    def test_rejects_unknown_missing_extra_and_wrongly_typed_payloads(self):
        invalid_calls = [
            ("unknown", {}),
            ("gather", {}),
            ("gather", {"torb_ids": [self.torb.pk], "extra": True}),
            ("gather", {"torb_ids": self.torb.pk}),
            ("gather", {"torb_ids": []}),
            ("gather", {"torb_ids": [str(self.torb.pk)]}),
            ("gather", {"torb_ids": [self.torb.pk, self.torb.pk]}),
            ("scout", {"target_colony_id": "1"}),
            ("end_turn", {"torb_ids": [self.torb.pk]}),
            ("purchase_discovery", {"discovery_id": "1"}),
        ]
        for action, payload in invalid_calls:
            with self.subTest(action=action, payload=payload):
                with self.assertRaises(ValueError):
                    self.perform(action, **payload)
        self.torb.refresh_from_db()
        self.colony.refresh_from_db()
        self.assertEqual(self.torb.action, Torb.Action.GATHERING)
        self.assertFalse(self.colony.ready)

    def test_rejects_foreign_dead_juvenile_and_infertile_torbs(self):
        foreign = TorbFactory()
        dead = TorbFactory(
            colony=self.colony,
            private_ID=2,
            is_alive=False,
            fertile=False,
            hp=0,
        )
        juvenile = TorbFactory(colony=self.colony, private_ID=3, growing=True)
        infertile = TorbFactory(colony=self.colony, private_ID=4, fertile=False)

        for action, ids in [
            ("gather", [foreign.pk]),
            ("enlist", [dead.pk]),
            ("research", [juvenile.pk]),
            ("breed", [self.torb.pk, infertile.pk]),
        ]:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    self.perform(action, torb_ids=ids)

    def test_rejects_unowned_colony_before_mutating(self):
        other = PlayerFactory()
        with self.assertRaises(PermissionDenied):
            ActionService.perform(
                player=other,
                colony=self.colony,
                action="gather",
                torb_ids=[self.torb.pk],
            )
        self.torb.refresh_from_db()
        self.assertEqual(self.torb.action, Torb.Action.GATHERING)

    def test_rejects_cross_game_self_and_undiscovered_attack_targets(self):
        cross_game = ColonyFactory()
        same_game = ColonyFactory(game=self.colony.game, name="Same game")
        story_count = StoryText.objects.count()

        for action, target_id in [
            ("scout", cross_game.pk),
            ("scout", self.colony.pk),
            ("attack", same_game.pk),
        ]:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    self.perform(action, target_colony_id=target_id)

        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.scout_target)
        self.assertIsNone(self.colony.army.attack_target)
        self.assertEqual(StoryText.objects.count(), story_count)

    def test_unaffordable_research_actions_preserve_resources_and_stories(self):
        discovery = DiscoveryFactory(research_cost=20)
        self.colony.lab.science_points = 10
        self.colony.lab.save(update_fields=["science_points"])
        story_count = StoryText.objects.count()

        for action, payload in [
            ("make_mutagen", {"science_points_used": 20}),
            ("purchase_discovery", {"discovery_id": discovery.pk}),
        ]:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    self.perform(action, **payload)

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 10)
        self.assertEqual(self.colony.lab.mutagen, 0)
        self.assertFalse(self.colony.lab.discoveries.exists())
        self.assertEqual(StoryText.objects.count(), story_count)
