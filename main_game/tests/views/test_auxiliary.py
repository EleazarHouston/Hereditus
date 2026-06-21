from django.test import TestCase
from django.urls import reverse

from main_game.tests.factories import ColonyFactory, TorbFactory


class ReadOnlyColonyViewTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.gatherer = TorbFactory(
            colony=self.colony,
            private_ID=1,
            action="gathering",
            fertile=True,
        )
        TorbFactory(
            colony=self.colony,
            private_ID=2,
            action="resting",
            fertile=False,
        )
        self.client.force_login(self.colony.player.user)

    def test_settings_context_and_get_only_contract(self):
        url = reverse("settings_view", args=[self.colony.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["colony"], self.colony)
        self.assertEqual(self.client.post(url).status_code, 405)

    def test_filter_torbs_returns_filtered_json_and_rejects_post(self):
        url = reverse("filter_torbs", args=[self.colony.pk])

        response = self.client.get(url, {"action": "gathering", "fertile": "fertile"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([torb["id"] for torb in payload["torbs"]], [self.gatherer.pk])
        self.assertIn("vitality", payload["gene_names"])
        self.assertEqual(self.client.post(url).status_code, 405)

    def test_filter_torbs_malformed_filters_are_harmless(self):
        url = reverse("filter_torbs", args=[self.colony.pk])

        response = self.client.get(url, {"action": "not-an-action", "fertile": "invalid"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["torbs"], [])

    def test_ready_status_returns_json_and_is_get_only(self):
        url = reverse("check_ready_status", args=[self.colony.pk])
        self.colony.ready = True
        self.colony.save(update_fields=["ready"])

        response = self.client.get(url)

        self.assertEqual(response.json(), {"ready": True})
        self.assertEqual(self.client.post(url).status_code, 405)

    def test_cross_colony_json_endpoints_are_forbidden(self):
        other = ColonyFactory()
        self.client.force_login(other.player.user)

        for name in ("filter_torbs", "check_ready_status"):
            with self.subTest(name=name):
                url = reverse(name, args=[self.colony.pk])
                self.assertEqual(self.client.get(url).status_code, 403)
