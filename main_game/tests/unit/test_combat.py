from unittest.mock import patch

from django.test import TestCase

from main_game.models import StoryText, Torb
from main_game.services.combat import CombatService
from main_game.tests.factories import ArmyTorbFactory, ColonyFactory, TorbFactory


class CombatRng:
    def __init__(self, *, uniforms=(), randrange_value=1, randint_value=0):
        self.uniforms = iter(uniforms)
        self.randrange_value = randrange_value
        self.randint_value = randint_value

    def uniform(self, start, end):
        return next(self.uniforms)

    def randrange(self, start, end):
        return self.randrange_value

    def randint(self, start, end):
        return min(max(self.randint_value, start), end)

    def choice(self, values):
        return values[0]


class CombatTargetingTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.target = ColonyFactory(game=self.colony.game, name="Target")

    def test_scout_target_can_be_set_and_cancelled(self):
        CombatService.set_target(colony=self.colony, action="scout", target_id=self.target.pk)
        self.colony.army.refresh_from_db()
        self.assertEqual(self.colony.army.scout_target, self.target)

        CombatService.set_target(colony=self.colony, action="scout", target_id=None)
        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.scout_target)

    def test_attack_requires_discovered_nonself_target(self):
        self.colony.army.set_attack_target(self.target.pk)
        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.attack_target)

        self.colony.discovered_colonies.add(self.target)
        self.colony.army.set_attack_target(self.target.pk)
        self.colony.army.refresh_from_db()
        self.assertEqual(self.colony.army.attack_target, self.target)

        self.colony.army.set_attack_target(self.colony.pk)
        self.colony.army.refresh_from_db()
        self.assertEqual(self.colony.army.attack_target, self.target)

    def test_scouting_undefended_colony_discovers_it(self):
        scout = TorbFactory(
            colony=self.colony,
            private_ID=1,
            action=Torb.Action.SOLDIERING,
        )
        ArmyTorbFactory(army=self.colony.army, torb=scout)
        self.colony.army.scout_target = self.target
        self.colony.army.save(update_fields=["scout_target"])

        result = self.colony.army.scout_colony(rng=CombatRng())

        self.assertTrue(result)
        self.assertTrue(self.colony.discovered_colonies.filter(pk=self.target.pk).exists())


class CombatResolutionTests(TestCase):
    def setUp(self):
        self.attacker = ColonyFactory()
        self.defender = ColonyFactory(game=self.attacker.game, name="Defender")
        self.attacker.army.morale = 50
        self.attacker.army.save(update_fields=["morale"])
        self.defender.army.morale = 50
        self.defender.army.save(update_fields=["morale"])

    def make_soldiers(self, *, enemy_hp=10):
        ally = TorbFactory(
            colony=self.attacker,
            private_ID=1,
            hp=10,
            max_hp=10,
            action=Torb.Action.SOLDIERING,
        )
        enemy = TorbFactory(
            colony=self.defender,
            private_ID=1,
            hp=enemy_hp,
            max_hp=10,
            action=Torb.Action.SOLDIERING,
        )
        ally_membership = ArmyTorbFactory(army=self.attacker.army, torb=ally)
        enemy_membership = ArmyTorbFactory(army=self.defender.army, torb=enemy)
        return ally_membership, enemy_membership

    def test_fight_applies_damage_and_adjusts_morale(self):
        ally, enemy = self.make_soldiers()
        rng = CombatRng(uniforms=[9, 5, 4, 1, 9, 1])

        self.attacker.army.torb_fight(ally, enemy, rng=rng)

        ally.torb.refresh_from_db()
        enemy.torb.refresh_from_db()
        self.attacker.army.refresh_from_db()
        self.defender.army.refresh_from_db()
        self.assertEqual(ally.torb.hp, 10)
        self.assertEqual(enemy.torb.hp, 2)
        self.assertEqual(self.attacker.army.morale, 51)
        self.assertEqual(self.defender.army.morale, 49)

    def test_combat_death_removes_enemy_from_army(self):
        ally, enemy = self.make_soldiers(enemy_hp=5)
        rng = CombatRng(uniforms=[9, 5, 4, 1, 9, 1])

        self.attacker.army.torb_fight(ally, enemy, rng=rng)

        enemy.torb.refresh_from_db()
        self.assertFalse(enemy.torb.is_alive)
        self.assertFalse(type(enemy).objects.filter(pk=enemy.pk).exists())

    def test_low_morale_retreats_without_fighting(self):
        self.make_soldiers()
        self.attacker.army.morale = 1
        self.attacker.army.save(update_fields=["morale"])
        rng = CombatRng(randrange_value=2)

        with patch.object(self.attacker.army, "torb_fight") as fight:
            result = self.attacker.army.battle_army(self.defender.army, rng=rng)

        self.assertFalse(result)
        fight.assert_not_called()

    def test_failed_scout_takes_bounded_damage(self):
        scout = TorbFactory(
            colony=self.attacker,
            private_ID=1,
            hp=5,
            max_hp=5,
            action=Torb.Action.SOLDIERING,
        )
        membership = ArmyTorbFactory(army=self.attacker.army, torb=scout)

        self.attacker.army._scout_failed(
            membership,
            self.defender,
            random_enemy_torb_power=8,
            random_ally_torb_resilience=3,
            rng=CombatRng(randint_value=3),
        )

        scout.refresh_from_db()
        self.assertEqual(scout.hp, 2)
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.attacker,
                story_text__contains="unknown colony",
            ).exists()
        )

    def test_failed_scout_accepts_standard_random_generator(self):
        scout = TorbFactory(
            colony=self.attacker,
            private_ID=1,
            hp=5,
            max_hp=5,
            action=Torb.Action.SOLDIERING,
        )
        membership = ArmyTorbFactory(army=self.attacker.army, torb=scout)

        self.attacker.army._scout_failed(
            membership,
            self.defender,
            random_enemy_torb_power=8.2,
            random_ally_torb_resilience=3.1,
            rng=__import__("random").Random(0),
        )

        scout.refresh_from_db()
        self.assertGreaterEqual(scout.hp, 0)
        self.assertLessEqual(scout.hp, 5)

    def test_morale_is_clamped(self):
        self.attacker.army.adjust_morale(1000)
        self.assertEqual(self.attacker.army.morale, 100)
        self.attacker.army.adjust_morale(-1000)
        self.assertEqual(self.attacker.army.morale, 0)

    def test_empty_colony_loot_is_zero(self):
        self.defender.food = 0
        self.defender.save(update_fields=["food"])

        self.attacker.army._attack_successful(self.defender, rng=CombatRng())

        self.attacker.refresh_from_db()
        self.defender.refresh_from_db()
        self.assertEqual(self.defender.food, 0)
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.attacker,
                story_text__contains="plundered 0 food",
            ).exists()
        )


class ArmyLifecycleTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()

    def test_training_adds_membership_and_purge_removes_non_soldier(self):
        torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            action=Torb.Action.TRAINING,
        )

        self.colony.army.train_soldiers(rng=CombatRng())

        torb.refresh_from_db()
        self.assertTrue(torb.trained)
        self.assertEqual(torb.action, Torb.Action.SOLDIERING)
        self.assertTrue(torb.army_torb.filter(army=self.colony.army).exists())

        torb.set_action(Torb.Action.RESTING)
        self.colony.army.purge_soldiers()
        self.assertFalse(torb.army_torb.exists())

    def test_army_aggregate_stats_use_active_soldiers(self):
        torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            hp=4,
            max_hp=5,
            action=Torb.Action.SOLDIERING,
        )
        ArmyTorbFactory(
            army=self.colony.army,
            torb=torb,
            active_alleles={"strength": 9, "agility": 4, "vitality": 16, "sturdiness": 4},
        )

        self.assertEqual(self.colony.army.army_health, 4)
        self.assertEqual(self.colony.army.army_power, 6)
        self.assertEqual(self.colony.army.army_resilience, 8)

    def test_scouting_without_soldiers_fails_cleanly(self):
        target = ColonyFactory(game=self.colony.game, name="Target")
        self.colony.army.scout_target = target
        self.colony.army.save(update_fields=["scout_target"])

        result = self.colony.army.scout_colony(rng=CombatRng())

        self.assertFalse(result)
        self.assertFalse(self.colony.discovered_colonies.filter(pk=target.pk).exists())

    def test_attack_on_undefended_colony_succeeds_and_clears_target(self):
        target = ColonyFactory(game=self.colony.game, name="Target", food=0)
        self.colony.discovered_colonies.add(target)
        torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            action=Torb.Action.SOLDIERING,
        )
        ArmyTorbFactory(army=self.colony.army, torb=torb)
        self.colony.army.set_attack_target(target.pk)

        self.colony.army.attack_colony(rng=CombatRng())

        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.attack_target)
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.colony,
                story_text__contains="glorious victory",
            ).exists()
        )
