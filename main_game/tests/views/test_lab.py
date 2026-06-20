from django.test import TestCase
from django.urls import reverse

from main_game.tests.factories import ColonyFactory, DiscoveryFactory, TorbFactory


class LabViewTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.user = self.colony.player.user
        self.torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            name="Grace",
            genes={"intelligence": [7, 8]},
        )
        self.url = reverse("lab_view", args=[self.colony.id])
        self.client.force_login(self.user)

    def test_lab_page_lists_torbs_and_available_discoveries(self):
        discovery = DiscoveryFactory(
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
        response = self.client.post(
            self.url,
            {
                "player-action": "research",
                "selected_torbs": [self.torb.id],
            },
        )

        self.assertRedirects(response, self.url)
        self.torb.refresh_from_db()
        self.assertEqual(self.torb.action, "researching")

    def test_mutagen_error_is_rendered_on_lab_page(self):
        response = self.client.post(
            self.url,
            {
                "player-action": "make_mutagen",
                "science_points_used": 10,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not enough science points to make mutagen.")
