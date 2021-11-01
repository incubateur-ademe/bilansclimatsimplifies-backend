from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import UserFactory


class TestUserApi(APITestCase):
    def test_unauthenticated_fetch_user(self):
        """
        When attempt to get user without being logged in, get 403
        """
        response = self.client.get(reverse("authenticated_user"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_authenticated_fetch_user(self):
        """
        If authenticated, should see only own details
        """
        UserFactory.create(username="other")
        response = self.client.get(reverse("authenticated_user"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["username"], authenticate.user.username)
