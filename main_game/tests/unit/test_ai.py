import random

from django.test import TestCase

from main_game.models import Torb
from main_game.services.ai import AIService
from main_game.tests.factories import AIPlayerFactory, ColonyFactory, TorbFactory


class AIDecisionTests(TestCase):
    def make_colony(self, **kwargs):
        return ColonyFactory(player=AIPlayerFactory(), **kwargs)

    def test_zero_population_only_readies_colony(self):
        colony = self.make_colony(food=0)

        AIService.make_decisions(colony, rng=random.Random(0))

        colony.refresh_from_db()
        self.assertTrue(colony.ready)
        self.assertEqual(colony.torb_count, 0)
        self.assertIsNone(colony.army.scout_target)
        self.assertIsNone(colony.army.attack_target)

    def test_just_enough_food_does_not_breed_small_population(self):
        colony = self.make_colony(food=5)
        torbs = [TorbFactory(colony=colony, private_ID=index) for index in range(1, 3)]

        AIService.make_decisions(colony, rng=random.Random(0))

        for torb in torbs:
            torb.refresh_from_db()
            self.assertEqual(torb.action, Torb.Action.GATHERING)

    def test_surplus_food_assigns_valid_breeding_pair(self):
        colony = self.make_colony(food=6)
        torbs = [TorbFactory(colony=colony, private_ID=index) for index in range(1, 3)]

        AIService.make_decisions(colony, rng=random.Random(0))

        for torb in torbs:
            torb.refresh_from_db()
        self.assertTrue(all(torb.action == Torb.Action.BREEDING for torb in torbs))
        self.assertEqual(torbs[0].context_torb_id, torbs[1].pk)
        self.assertEqual(torbs[1].context_torb_id, torbs[0].pk)

    def test_population_boundary_enlists_only_available_gatherer(self):
        colony = self.make_colony(food=5)
        torbs = [TorbFactory(colony=colony, private_ID=index) for index in range(1, 8)]

        AIService.make_decisions(colony, rng=random.Random(0))

        actions = []
        for torb in torbs:
            torb.refresh_from_db()
            actions.append(torb.action)
        self.assertEqual(actions.count(Torb.Action.TRAINING), 1)
        self.assertEqual(actions.count(Torb.Action.GATHERING), 6)

    def test_soldier_scouts_valid_undiscovered_colony(self):
        colony = self.make_colony(food=0)
        target = ColonyFactory(game=colony.game, name="Target")
        TorbFactory(
            colony=colony,
            private_ID=1,
            action=Torb.Action.SOLDIERING,
            hp=4,
            max_hp=5,
        )

        AIService.make_decisions(colony, rng=random.Random(0))

        colony.army.refresh_from_db()
        self.assertEqual(colony.army.scout_target, target)
        self.assertIsNone(colony.army.attack_target)

    def test_healthy_soldier_attacks_valid_discovered_colony(self):
        colony = self.make_colony(food=0)
        target = ColonyFactory(game=colony.game, name="Target")
        colony.discovered_colonies.add(target)
        TorbFactory(
            colony=colony,
            private_ID=1,
            action=Torb.Action.SOLDIERING,
            hp=5,
            max_hp=5,
        )

        AIService.make_decisions(colony, rng=random.Random(0))

        colony.army.refresh_from_db()
        self.assertIsNone(colony.army.scout_target)
        self.assertEqual(colony.army.attack_target, target)
