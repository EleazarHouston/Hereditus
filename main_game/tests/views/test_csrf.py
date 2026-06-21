from django.test import Client, TestCase
from django.urls import reverse

from main_game.tests.factories import ColonyFactory, GameFactory


class CsrfEnforcementTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.game = GameFactory()

    def test_protected_gameplay_posts_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.colony.player.user)
        requests = [
            (
                reverse("colony_view", args=[self.colony.pk]),
                {"player-action": "gather", "selected_torbs": []},
            ),
            (reverse("army_view", args=[self.colony.pk]), {"player-action": "scout"}),
            (
                reverse("lab_view", args=[self.colony.pk]),
                {"player-action": "make_mutagen", "science_points_used": 10},
            ),
            (
                reverse("play"),
                {"game_id": self.game.pk, "colony_name": "No CSRF"},
            ),
            (reverse("logout"), {}),
        ]

        for url, data in requests:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, data).status_code, 403)

    def test_public_authentication_posts_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        requests = [
            (reverse("login"), {"username": "x", "password": "y"}),
            (
                reverse("register"),
                {"username": "x", "password1": "Password123!", "password2": "Password123!"},
            ),
        ]

        for url, data in requests:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, data).status_code, 403)
