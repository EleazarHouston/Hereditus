from django.test import TestCase

from main_game.models import StoryText
from main_game.services.actions import ActionService
from main_game.services.research import ResearchService
from main_game.tests.factories import ColonyFactory, DiscoveryFactory, TorbFactory


class LabModelTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.player = self.colony.player

    def make_torb(self, **kwargs):
        defaults = {
            "colony": self.colony,
            "private_ID": 1,
            "name": "Ada",
            "genes": {"intelligence": [4, 6]},
        }
        defaults.update(kwargs)
        return TorbFactory(**defaults)

    def test_conduct_research_supports_torbs_without_intelligence(self):
        self.make_torb(genes={}, action="researching")

        ResearchService.conduct_research(self.colony.lab)

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 1)
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.colony,
                story_text="Your Torbs gleaned 1 science.",
            ).exists()
        )

    def test_make_mutagen_spends_science_and_records_story(self):
        self.colony.lab.science_points = 30
        self.colony.lab.save()

        ActionService.perform(
            player=self.player,
            colony=self.colony,
            action="make_mutagen",
            science_points_used=20,
        )

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 10)
        self.assertEqual(self.colony.lab.mutagen, 2)
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.colony,
                story_text="Your lab made 2 mutagen.",
            ).exists()
        )

    def test_make_mutagen_rejects_less_than_ten_science(self):
        self.colony.lab.science_points = 30
        self.colony.lab.save()

        with self.assertRaisesMessage(ValueError, "positive multiple of 10"):
            ResearchService.make_mutagen(self.colony.lab, 0)

    def test_unlock_discovery_spends_science_and_prevents_repeat_purchase(self):
        discovery = DiscoveryFactory(
            name="Genomics",
            description="Read Torb genomes.",
            research_cost=20,
        )
        self.colony.lab.science_points = 25
        self.colony.lab.save()

        ActionService.perform(
            player=self.player,
            colony=self.colony,
            action="purchase_discovery",
            discovery_id=discovery.id,
        )

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 5)
        self.assertTrue(self.colony.lab.discoveries.filter(pk=discovery.pk).exists())
        with self.assertRaisesMessage(ValueError, "Discovery already unlocked"):
            ResearchService.unlock_discovery(self.colony.lab, discovery)

    def test_rest_torbs_uses_percentage_of_max_hp(self):
        torb = self.make_torb(action="resting", hp=1, max_hp=10)

        self.colony.rest_torbs()

        torb.refresh_from_db()
        self.assertEqual(torb.hp, 5)
