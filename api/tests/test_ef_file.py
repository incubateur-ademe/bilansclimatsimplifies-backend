from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


class TestEmissionFactorsFileApi(APITestCase):
    def test_ef_file(self):
        """
        Test that endpoint returns json emissions file
        """
        response = self.client.get(reverse("ef-file"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertGreaterEqual(len(body.keys()), 200)
