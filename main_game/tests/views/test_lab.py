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


class LabViewIntegrationTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.torb = TorbFactory(colony=self.colony, private_ID=1)
        self.discovery = DiscoveryFactory(research_cost=10)
        self.url = reverse("lab_view", args=[self.colony.pk])
        self.client.force_login(self.colony.player.user)

    def test_context_separates_unlocked_and_available_discoveries(self):
        unlocked = DiscoveryFactory(name="Unlocked", research_cost=1)
        self.colony.lab.discoveries.add(unlocked)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["unlocked_discoveries"]), [unlocked])
        self.assertIn(self.discovery, response.context["available_discoveries"])
        self.assertEqual(list(response.context["torbs"]), [self.torb])

    def test_valid_mutagen_and_discovery_posts_redirect_with_messages(self):
        self.colony.lab.science_points = 20
        self.colony.lab.save(update_fields=["science_points"])

        mutagen = self.client.post(
            self.url,
            {"player-action": "make_mutagen", "science_points_used": 10},
            follow=True,
        )
        discovery = self.client.post(
            self.url,
            {"player-action": "purchase_discovery", "discovery_id": self.discovery.pk},
            follow=True,
        )

        self.assertRedirects(mutagen, self.url)
        self.assertRedirects(discovery, self.url)
        self.assertContains(mutagen, "Lab action completed.")
        self.assertContains(discovery, "Lab action completed.")
        self.colony.lab.refresh_from_db()
        self.assertEqual(self.colony.lab.mutagen, 1)
        self.assertEqual(self.colony.lab.science_points, 0)
        self.assertTrue(self.colony.lab.discoveries.filter(pk=self.discovery.pk).exists())

    def test_malformed_and_missing_discovery_posts_render_errors(self):
        malformed = self.client.post(
            self.url,
            {"player-action": "make_mutagen", "science_points_used": "invalid"},
        )
        missing = self.client.post(
            self.url,
            {"player-action": "purchase_discovery", "discovery_id": 999999},
        )

        self.assertEqual(malformed.status_code, 200)
        self.assertContains(malformed, "Invalid lab action.")
        self.assertEqual(missing.status_code, 200)
        self.assertTrue(missing.context["error_message"])

    def test_cross_colony_torb_is_rejected_without_mutation(self):
        foreign = TorbFactory()

        response = self.client.post(
            self.url,
            {"player-action": "research", "selected_torbs": [foreign.pk]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid lab action.")
        foreign.refresh_from_db()
        self.assertEqual(foreign.action, "gathering")

    def test_lab_accepts_only_get_and_post(self):
        self.assertEqual(self.client.put(self.url).status_code, 405)
