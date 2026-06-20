from django.test import TestCase

from main_game.models import StoryText, Torb
from main_game.tests.factories import ArmyTorbFactory, ColonyFactory, TorbFactory


class TorbLifecycleTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()

    def test_action_transitions_update_description(self):
        torb = TorbFactory(colony=self.colony, private_ID=1)

        torb.set_action(Torb.Action.RESEARCHING)
        self.assertEqual(torb.action, Torb.Action.RESEARCHING)
        self.assertEqual(torb.action_desc, "🔬 Researching")

        torb.set_action(Torb.Action.RESTING)
        self.assertEqual(torb.action, Torb.Action.RESTING)
        self.assertEqual(torb.action_desc, "💤 Resting")

    def test_dead_and_growing_torbs_cannot_be_assigned_other_actions(self):
        dead = TorbFactory(
            colony=self.colony,
            private_ID=1,
            is_alive=False,
            fertile=False,
            hp=0,
        )
        growing = TorbFactory(colony=self.colony, private_ID=2, growing=True)

        dead.set_action(Torb.Action.GATHERING)
        growing.set_action(Torb.Action.SOLDIERING)

        self.assertEqual(dead.action, Torb.Action.DEAD)
        self.assertEqual(growing.action, Torb.Action.GROWING)

    def test_adjust_hp_clamps_to_bounds(self):
        torb = TorbFactory(colony=self.colony, private_ID=1, hp=3, max_hp=5)

        torb.adjust_hp(100)
        self.assertEqual(torb.hp, 5)
        torb.adjust_hp(-2)
        self.assertEqual(torb.hp, 3)

    def test_death_marks_torb_infertile_and_removes_army_membership(self):
        torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            hp=2,
            max_hp=5,
            action=Torb.Action.SOLDIERING,
        )
        membership = ArmyTorbFactory(army=self.colony.army, torb=torb)

        torb.adjust_hp(-2, context="a test")

        torb.refresh_from_db()
        self.assertEqual(torb.hp, 0)
        self.assertFalse(torb.is_alive)
        self.assertFalse(torb.fertile)
        self.assertEqual(torb.action, Torb.Action.DEAD)
        self.assertFalse(type(membership).objects.filter(pk=membership.pk).exists())
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.colony,
                story_text=f"'{torb.name}' (Torb {torb.private_ID}) died from a test.",
            ).exists()
        )

    def test_reassigning_breeder_clears_partner(self):
        first = TorbFactory(colony=self.colony, private_ID=1)
        second = TorbFactory(colony=self.colony, private_ID=2)
        first.set_action(Torb.Action.BREEDING, context_torb=second)
        second.set_action(Torb.Action.BREEDING, context_torb=first)

        first.set_action(Torb.Action.RESTING)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.action, Torb.Action.RESTING)
        self.assertIsNone(first.context_torb)
        self.assertEqual(second.action, Torb.Action.GATHERING)
        self.assertIsNone(second.context_torb)


class TorbDerivedStateTests(TestCase):
    def test_power_resilience_and_status_reflect_genes_and_state(self):
        torb = TorbFactory(
            colony=ColonyFactory(),
            private_ID=1,
            genes={
                "strength": [9],
                "agility": [4],
                "vitality": [16],
                "sturdiness": [4],
                "intelligence": [1],
            },
        )

        self.assertEqual(torb.power, 6)
        self.assertEqual(torb.resilience, 8)
        self.assertEqual(torb.status, "Alive<br>Fertile")

        torb.starving = True
        torb.fertile = False
        torb.growing = True
        self.assertEqual(torb.status, "Starving<br>Infertile<br>Juvenile")

        torb.is_alive = False
        self.assertEqual(torb.status, "Dead<br>Infertile<br>Juvenile")
