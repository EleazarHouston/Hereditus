from django.test import TestCase
from django.urls import reverse

from main_game.models import Colony
from main_game.tests.factories import ColonyFactory, GameFactory, UserFactory


class PlayViewTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("play")
        self.client.force_login(self.user)

    def test_get_lists_owned_colonies_and_accessible_games(self):
        owned = ColonyFactory(player__user=self.user)
        public = GameFactory(private=False)
        allowed = GameFactory(private=True)
        allowed.allowed_players.add(self.user)
        hidden = GameFactory(private=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(owned, response.context["colonies"])
        self.assertIn(public, response.context["games"])
        self.assertIn(allowed, response.context["games"])
        self.assertNotIn(hidden, response.context["games"])

    def test_valid_join_redirects_creates_colony_and_flashes(self):
        game = GameFactory()

        response = self.client.post(
            self.url,
            {"game_id": game.pk, "colony_name": "New colony"},
            follow=True,
        )

        self.assertRedirects(response, self.url)
        self.assertContains(response, "Colony created.")
        self.assertTrue(
            Colony.objects.filter(game=game, player__user=self.user, name="New colony").exists()
        )

    def test_malformed_closed_and_capacity_posts_do_not_create(self):
        malformed = self.client.post(self.url, {"game_id": "invalid"})
        self.assertEqual(malformed.status_code, 200)
        self.assertTrue(malformed.context["error_message"])

        closed = GameFactory(closed=True)
        closed_response = self.client.post(
            self.url,
            {"game_id": closed.pk, "colony_name": "Rejected"},
        )
        self.assertContains(closed_response, "closed")
        self.assertFalse(closed.colony_set.exists())

        game = GameFactory(max_colonies_per_player=1)
        ColonyFactory(game=game, player__user=self.user)
        count = Colony.objects.count()
        capped = self.client.post(
            self.url,
            {"game_id": game.pk, "colony_name": "Too many"},
        )
        self.assertContains(capped, "max number")
        self.assertEqual(Colony.objects.count(), count)

    def test_play_accepts_only_get_and_post(self):
        self.assertEqual(self.client.put(self.url).status_code, 405)
