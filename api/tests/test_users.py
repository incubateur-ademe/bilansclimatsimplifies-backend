from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import UserFactory
from unittest.mock import patch
import requests_mock
from django.test.utils import override_settings


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

    @requests_mock.Mocker()
    @override_settings(AUTH_USERS_API="https://example.com")
    @override_settings(AUTH_PASS_REDIRECT_URI="https://home.com")
    @override_settings(AUTH_KEYCLOAK="https://keycloak.com")
    @override_settings(AUTH_REALM="test")
    @override_settings(AUTH_CLIENT_ID="hello")
    @override_settings(AUTH_CLIENT_SECRET="supersecret")
    def test_account_creation(self, request_mock):
        """
        Test that the endpoint calls the account creation endpoints
        """
        payload = {
            "email": "test@example.com",
            "firstname": "Camille",
            "lastname": "Dupont",
            "cgu": "true",
        }
        token_mocker = request_mock.post(
            "https://keycloak.com/auth/realms/test/protocol/openid-connect/token",
            json={"access_token": "myaccesstoken"},
        )
        search_mocker = request_mock.get("https://example.com/api/users/search", status_code=status.HTTP_404_NOT_FOUND)
        create_mocker = request_mock.post(
            "https://example.com/api/users", status_code=status.HTTP_201_CREATED, json={"userId": 42}
        )
        cgu_mocker = request_mock.put("https://example.com/api/users/42/enableCGU", status_code=status.HTTP_200_OK)

        response = self.client.post(reverse("create_account"), payload, format="json")

        self.assertTrue(token_mocker.called_once)
        self.assertEqual(
            token_mocker.last_request.text, "client_id=hello&client_secret=supersecret&grant_type=client_credentials"
        )
        self.assertTrue(search_mocker.called_once)
        self.assertEqual(search_mocker.last_request.qs, {"email": ["test@example.com"]})
        self.assertTrue(create_mocker.called_once)
        self.assertEqual(
            create_mocker.last_request.json(),
            {
                "email": "test@example.com",
                "firstname": "Camille",
                "lastname": "Dupont",
            },
        )
        self.assertTrue(cgu_mocker.called_once)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # user not created in DB at this point - will be created on first login
