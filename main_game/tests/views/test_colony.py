from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from main_game.models import Torb
from main_game.services.actions import ActionService
from main_game.tests.factories import ColonyFactory, TorbFactory


class ColonyViewTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            action=Torb.Action.RESTING,
        )
        self.url = reverse("colony_view", args=[self.colony.pk])
        self.client.force_login(self.colony.player.user)

    def test_get_returns_expected_context(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["colony"], self.colony)
        self.assertEqual(response.context["num_torbs"], 1)
        self.assertEqual(list(response.context["torbs"]), [self.torb])
        self.assertIn("vitality", response.context["gene_names"])
        self.assertIn("Resting", response.context["unique_actions"])
        self.assertContains(response, self.torb.name)

    def test_valid_action_redirects_updates_state_and_flashes_success(self):
        response = self.client.post(
            self.url,
            {"player-action": "gather", "selected_torbs": [self.torb.pk]},
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertContains(response, "Colony action updated.")
        self.torb.refresh_from_db()
        self.assertEqual(self.torb.action, Torb.Action.GATHERING)

    def test_end_turn_uses_payload_without_torb_ids(self):
        with patch.object(ActionService, "perform") as perform:
            response = self.client.post(self.url, {"player-action": "end_turn"})

        self.assertRedirects(response, self.url)
        perform.assert_called_once_with(
            player=self.colony.player,
            colony=self.colony,
            action="end_turn",
        )

    def test_malformed_action_redirects_with_error_and_no_change(self):
        response = self.client.post(
            self.url,
            {"player-action": "gather"},
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertContains(response, "torb_ids must be a non-empty list")
        self.torb.refresh_from_db()
        self.assertEqual(self.torb.action, Torb.Action.RESTING)

    def test_cross_colony_torb_id_is_rejected_by_form(self):
        foreign = TorbFactory()

        response = self.client.post(
            self.url,
            {"player-action": "gather", "selected_torbs": [foreign.pk]},
            follow=True,
        )

        self.assertContains(response, "Invalid colony action.")
        foreign.refresh_from_db()
        self.assertEqual(foreign.action, Torb.Action.GATHERING)

    def test_non_owner_post_is_forbidden(self):
        other = ColonyFactory()
        self.client.force_login(other.player.user)

        response = self.client.post(
            self.url,
            {"player-action": "gather", "selected_torbs": [self.torb.pk]},
        )

        self.assertEqual(response.status_code, 403)
        self.torb.refresh_from_db()
        self.assertEqual(self.torb.action, Torb.Action.RESTING)
