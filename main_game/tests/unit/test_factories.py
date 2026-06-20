from django.test import TestCase

from main_game.tests.factories import (
    AIPlayerFactory,
    ArmyFactory,
    ArmyTorbFactory,
    ColonyFactory,
    DiscoveryFactory,
    LabFactory,
    TorbFactory,
)


class FactoryTests(TestCase):
    def test_core_factories_build_consistent_relations(self):
        colony = ColonyFactory()
        lab = LabFactory(colony=colony, science_points=25)
        army = ArmyFactory(colony=colony, morale=75)
        torb = TorbFactory(colony=colony)
        army_torb = ArmyTorbFactory(army=army, torb=torb)
        discovery = DiscoveryFactory()
        ai_player = AIPlayerFactory()

        self.assertEqual(lab.colony, colony)
        self.assertEqual(lab.science_points, 25)
        self.assertEqual(army.colony, colony)
        self.assertEqual(army.morale, 75)
        self.assertEqual(army_torb.torb.colony, colony)
        self.assertTrue(discovery.name)
        self.assertIsNone(ai_player.user)
