from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Colony, Discovery, Game, Player, StoryText, Torb


class LabModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="researcher", password="test-password")
        self.player = Player.objects.create(user=self.user)
        self.game = Game.objects.create(description="Test game", starting_torbs=0)
        self.colony = Colony.objects.create(
            name="Test colony",
            game=self.game,
            player=self.player,
        )

    def make_torb(self, **kwargs):
        defaults = {
            "colony": self.colony,
            "private_ID": 1,
            "name": "Ada",
            "genes": {"intelligence": [4, 6]},
        }
        defaults.update(kwargs)
        return Torb.objects.create(**defaults)

    @patch("main_game.models.lab.random.random", return_value=0)
    def test_conduct_research_supports_torbs_without_intelligence(self, _random):
        self.make_torb(genes={}, action="researching")

        self.colony.lab.conduct_research()

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

        self.player.perform_action(
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

        with self.assertRaisesMessage(ValueError, "Not enough science points"):
            self.colony.lab.make_mutagen(0)

    def test_unlock_discovery_spends_science_and_prevents_repeat_purchase(self):
        discovery = Discovery.objects.create(
            name="Genomics",
            description="Read Torb genomes.",
            research_cost=20,
        )
        self.colony.lab.science_points = 25
        self.colony.lab.save()

        self.player.perform_action(
            colony=self.colony,
            action="purchase_discovery",
            discovery_id=discovery.id,
        )

        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.science_points, 5)
        self.assertTrue(self.colony.lab.discoveries.filter(pk=discovery.pk).exists())
        with self.assertRaisesMessage(ValueError, "Discovery already unlocked"):
            self.colony.lab.unlock_discovery(discovery)

    def test_rest_torbs_uses_percentage_of_max_hp(self):
        torb = self.make_torb(action="resting", hp=1, max_hp=10)

        self.colony.rest_torbs()

        torb.refresh_from_db()
        self.assertEqual(torb.hp, 5)


class LabViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="test-password")
        self.player = Player.objects.create(user=self.user)
        self.game = Game.objects.create(description="Test game", starting_torbs=0)
        self.colony = Colony.objects.create(
            name="Test colony",
            game=self.game,
            player=self.player,
        )
        self.torb = Torb.objects.create(
            colony=self.colony,
            private_ID=1,
            name="Grace",
            genes={"intelligence": [7, 8]},
        )
        self.url = reverse("lab_view", args=[self.colony.id])
        self.client.force_login(self.user)

    def test_lab_page_lists_torbs_and_available_discoveries(self):
        discovery = Discovery.objects.create(
            name="Biochemistry",
            description="Create useful compounds.",
            research_cost=50,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.torb.name)
        self.assertContains(response, discovery.name)
        self.assertContains(response, "Year: 1")

    def test_research_post_assigns_torb_and_redirects_to_lab(self):
        response = self.client.post(self.url, {
            "player-action": "research",
            "selected_torbs": [self.torb.id],
        })

        self.assertRedirects(response, self.url)
        self.torb.refresh_from_db()
        self.assertEqual(self.torb.action, "researching")

    def test_mutagen_error_is_rendered_on_lab_page(self):
        response = self.client.post(self.url, {
            "player-action": "make_mutagen",
            "science_points_used": 10,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not enough science points to make mutagen.")
