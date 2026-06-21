from django.test import TestCase
from django.urls import reverse

from main_game.tests.factories import ColonyFactory, TorbFactory


class ArmyViewTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.target = ColonyFactory(game=self.colony.game, name="Target")
        TorbFactory(colony=self.colony, private_ID=1, action="soldiering")
        TorbFactory(colony=self.colony, private_ID=2, action="training")
        self.url = reverse("army_view", args=[self.colony.pk])
        self.client.force_login(self.colony.player.user)

    def test_get_returns_army_context(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["colony"], self.colony)
        self.assertEqual(response.context["num_soldiers"], 1)
        self.assertEqual(response.context["num_training"], 1)
        self.assertIn(self.target, response.context["all_colonies"])

    def test_valid_scout_redirects_sets_target_and_flashes_success(self):
        response = self.client.post(
            self.url,
            {"player-action": "scout", "selected_colony": self.target.pk},
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertContains(response, "Army orders updated.")
        self.colony.army.refresh_from_db()
        self.assertEqual(self.colony.army.scout_target, self.target)

    def test_malformed_post_redirects_with_flash(self):
        response = self.client.post(
            self.url,
            {"player-action": "scout", "selected_colony": "invalid"},
            follow=True,
        )

        self.assertContains(response, "Invalid army action.")
        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.scout_target)

    def test_cross_game_target_is_rejected_without_mutation(self):
        cross_game = ColonyFactory()

        response = self.client.post(
            self.url,
            {"player-action": "scout", "selected_colony": cross_game.pk},
            follow=True,
        )

        self.assertContains(response, "same game")
        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.scout_target)

    def test_undiscovered_attack_is_rejected(self):
        response = self.client.post(
            self.url,
            {"player-action": "attack", "selected_colony": self.target.pk},
            follow=True,
        )

        self.assertContains(response, "must be discovered")
        self.colony.army.refresh_from_db()
        self.assertIsNone(self.colony.army.attack_target)

    def test_method_and_owner_boundaries(self):
        self.assertEqual(self.client.put(self.url).status_code, 405)
        other = ColonyFactory()
        self.client.force_login(other.player.user)
        self.assertEqual(
            self.client.post(self.url, {"player-action": "scout"}).status_code,
            403,
        )
