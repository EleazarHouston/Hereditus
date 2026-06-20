import random

from django.db import IntegrityError, transaction
from django.test import TestCase

from main_game.models import StoryText, Torb
from main_game.tests.factories import ArmyTorbFactory, ColonyFactory, TorbFactory


class BreedingValidationTests(TestCase):
    def test_rejects_foreign_and_dead_torbs(self):
        colony = ColonyFactory()
        foreign = TorbFactory()
        local = TorbFactory(colony=colony, private_ID=1)
        dead = TorbFactory(colony=colony, private_ID=2, is_alive=False, fertile=False, hp=0)

        with self.assertRaises(ValueError):
            colony.set_breed_torbs([local.pk, foreign.pk])
        with self.assertRaises(ValueError):
            colony.set_breed_torbs([local.pk, dead.pk])


class CombatRegressionTests(TestCase):
    def test_stalemate_terminates(self):
        attacker = ColonyFactory()
        defender = ColonyFactory(game=attacker.game, name="Defender")
        ally = TorbFactory(colony=attacker, private_ID=1, action=Torb.Action.SOLDIERING)
        enemy = TorbFactory(colony=defender, private_ID=1, action=Torb.Action.SOLDIERING)
        ArmyTorbFactory(
            army=attacker.army,
            torb=ally,
            active_alleles={"strength": 1, "agility": 1, "vitality": 1, "sturdiness": 1},
        )
        ArmyTorbFactory(
            army=defender.army,
            torb=enemy,
            active_alleles={"strength": 1, "agility": 1, "vitality": 1, "sturdiness": 1},
        )

        self.assertFalse(attacker.army.battle_army(defender.army, rng=random.Random(0)))

    def test_loot_handles_zero_width_range(self):
        attacker = ColonyFactory(food=0)
        defender = ColonyFactory(game=attacker.game, name="Defender", food=1)
        torb = TorbFactory(colony=attacker, private_ID=1, action=Torb.Action.SOLDIERING)
        ArmyTorbFactory(army=attacker.army, torb=torb)

        attacker.army._attack_successful(defender, rng=random.Random(0))

        attacker.refresh_from_db()
        defender.refresh_from_db()
        self.assertEqual(attacker.food, 1)
        self.assertEqual(defender.food, 0)

    def test_scout_message_uses_requested_target(self):
        colony = ColonyFactory()
        old_target = ColonyFactory(game=colony.game, name="Old")
        requested = ColonyFactory(game=colony.game, name="Requested")
        colony.army.scout_target = old_target
        colony.army.save(update_fields=["scout_target"])
        colony.discovered_colonies.add(requested)

        colony.army.set_scout_target(requested.pk)

        self.assertTrue(
            StoryText.objects.filter(
                colony=colony,
                story_text=f"Our new scout target is {requested.name}.",
            ).exists()
        )


class ConstraintTests(TestCase):
    def test_negative_food_and_duplicate_private_id_are_rejected(self):
        colony = ColonyFactory()
        TorbFactory(colony=colony, private_ID=1)

        with self.assertRaises(IntegrityError), transaction.atomic():
            type(colony).objects.filter(pk=colony.pk).update(food=-1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            TorbFactory(colony=colony, private_ID=1)
