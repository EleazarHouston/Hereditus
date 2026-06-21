from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from main_game.tests.factories import UserFactory


class AuthenticationViewTests(TestCase):
    def test_main_page_and_protected_play_redirects(self):
        self.assertEqual(self.client.get(reverse("main_page")).status_code, 200)
        response = self.client.get(reverse("play"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_registration_valid_invalid_and_authenticated_paths(self):
        url = reverse("register")
        self.assertIn("form", self.client.get(url).context)

        invalid = self.client.post(
            url,
            {"username": "new-user", "password1": "one", "password2": "two"},
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertFalse(User.objects.filter(username="new-user").exists())
        self.assertTrue(invalid.context["form"].errors)

        valid = self.client.post(
            url,
            {
                "username": "new-user",
                "password1": "ComplexPass984!Z",
                "password2": "ComplexPass984!Z",
            },
            follow=True,
        )
        self.assertRedirects(valid, reverse("play"))
        self.assertContains(valid, "Registration complete.")
        self.assertTrue(valid.wsgi_request.user.is_authenticated)

        self.assertRedirects(self.client.get(url), reverse("play"))

    def test_login_valid_invalid_and_authenticated_paths(self):
        user = UserFactory()
        url = reverse("login")
        self.assertIn("form", self.client.get(url).context)

        invalid = self.client.post(
            url,
            {"username": user.username, "password": "wrong"},
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertTrue(invalid.context["form"].errors)

        valid = self.client.post(
            url,
            {"username": user.username, "password": "test-password"},
            follow=True,
        )
        self.assertRedirects(valid, reverse("play"))
        self.assertContains(valid, "Logged in.")
        self.assertTrue(valid.wsgi_request.user.is_authenticated)
        self.assertRedirects(self.client.get(url), reverse("play"))

    def test_logout_requires_login_and_post_then_flashes(self):
        url = reverse("logout")
        self.assertIn(reverse("login"), self.client.post(url).url)

        self.client.force_login(UserFactory())
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, follow=True)

        self.assertRedirects(response, reverse("main_page"))
        self.assertContains(response, "Logged out.")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_auth_pages_reject_unsupported_methods(self):
        self.assertEqual(self.client.put(reverse("login")).status_code, 405)
        self.assertEqual(self.client.put(reverse("register")).status_code, 405)
        self.assertEqual(self.client.post(reverse("main_page")).status_code, 405)
