from django.test import TestCase
from django.urls import reverse

from main_game.tests.factories import ColonyFactory, PlayerFactory


class ColonyViewAuthorizationTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.other_player = PlayerFactory()
        self.urls = [
            reverse("colony_view", args=[self.colony.pk]),
            reverse("army_view", args=[self.colony.pk]),
            reverse("settings_view", args=[self.colony.pk]),
            reverse("lab_view", args=[self.colony.pk]),
            reverse("filter_torbs", args=[self.colony.pk]),
            reverse("check_ready_status", args=[self.colony.pk]),
        ]

    def test_anonymous_users_are_redirected_to_login(self):
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_non_owners_receive_permission_denied(self):
        self.client.force_login(self.other_player.user)
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_owner_can_access_every_colony_endpoint(self):
        self.client.force_login(self.colony.player.user)
        for url in self.urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
