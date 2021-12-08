from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import UserFactory
from unittest.mock import patch


class TestUserApi(APITestCase):
    def test_unauthenticated_fetch_user(self):
        """
        When attempt to get user without being logged in, get 403
        """
        response = self.client.get(reverse("ademe_user"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_authenticated_fetch_user(self):
        """
        If authenticated, should see only own details
        """
        UserFactory.create(username="other")
        response = self.client.get(reverse("ademe_user"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["username"], authenticate.user.username)
        self.assertIn("isStaff", body)

    def test_create_ademe_user(self):
        """
        A user is created from JWT if it doesn't exist
        """
        self.assertEqual(get_user_model().objects.count(), 0)
        mock_token = {
            "preferred_username": "test",
            "email": "test@example.com",
            "given_name": "Camille",
            "family_name": "Dupont",
            "sub": "test-ademe-id",
        }
        response = None
        with patch("api.views.AdemeUserView._get_token", return_value=mock_token):
            response = self.client.post(reverse("ademe_user"), {"token": "test_token"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.first()
        self.assertEqual(user.ademe_id, "test-ademe-id")
        self.assertEqual(user.username, "test")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Camille")
        self.assertEqual(user.last_name, "Dupont")

    def test_update_ademe_user(self):
        """
        An existing user gets updated from JWT on login
        """
        UserFactory.create(
            ademe_id="test-ademe-id",
            username="other",
            email="other@example.com",
            first_name="Other",
            last_name="Other",
        )
        mock_token = {
            "preferred_username": "test",
            "email": "test@example.com",
            "given_name": "Camille",
            "family_name": "Dupont",
            "sub": "test-ademe-id",
        }
        response = None
        with patch("api.views.AdemeUserView._get_token", return_value=mock_token):
            response = self.client.post(reverse("ademe_user"), {"token": "test_token"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.first()
        self.assertEqual(user.ademe_id, "test-ademe-id")
        self.assertEqual(user.username, "test")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Camille")
        self.assertEqual(user.last_name, "Dupont")

    def test_missing_token(self):
        """
        400 if token missing on POST
        """
        response = self.client.post(reverse("ademe_user"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
