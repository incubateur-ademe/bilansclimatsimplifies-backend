from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import ReportFactory, EmissionFactory
from data.models import Emission


class TestEmissionApi(APITestCase):
    def test_unauthenticated_create_emission(self):
        """
        Should not be able to create an emission if not logged in
        """
        self.assertEqual(len(Emission.objects.all()), 0)

        response = self.client.post(reverse("emissions"), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(len(Emission.objects.all()), 0)

    @authenticate
    def test_unauthorised_create_emission(self):
        """
        Should not be able to create an emission for a report user doesn't manage
        """
        self.assertEqual(len(Emission.objects.all()), 0)
        wrong_report = ReportFactory.create()
        ReportFactory.create(gestionnaire=authenticate.user)

        response = self.client.post(
            reverse("emissions"),
            {
                "bilan": wrong_report.id,
                "type": "petrole",
                "valeur": 100,
                "unite": "l",
                "poste": 1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(Emission.objects.all()), 0)

    @authenticate
    def test_create_emission_nonexistant_report(self):
        """
        Should not be able to create an emission for a nonexistant report
        """
        self.assertEqual(len(Emission.objects.all()), 0)

        response = self.client.post(
            reverse("emissions"),
            {
                "bilan": 90,
                "type": "petrole",
                "valeur": 100,
                "unite": "l",
                "poste": 1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(Emission.objects.all()), 0)

    @authenticate
    def test_create_emission(self):
        """
        Should be able to create emission for report the authenticated user manages
        """
        self.assertEqual(len(Emission.objects.all()), 0)
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        payload = {
            "bilan": my_report.id,
            "type": "petrole",
            "valeur": 100,
            "unite": "l",
            "poste": 1,
        }
        response = self.client.post(reverse("emissions"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        emissions = Emission.objects.all()
        self.assertEqual(len(emissions), 1)
        body = response.json()
        self.assertEqual(body["id"], emissions[0].id)
        # TODO: check conversion for emission and new total for scope is in response

    def test_unauthenticated_fetch_report_emissions(self):
        """
        403 if not logged in
        """
        response = self.client.get(reverse("report_emissions", kwargs={"report_pk": 90}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_unauthorised_fetch_report_emissions(self):
        """
        404 if not manager of the report
        """
        not_my_report = ReportFactory.create()
        EmissionFactory.create(bilan=not_my_report)
        EmissionFactory.create(bilan=not_my_report)

        response = self.client.get(reverse("report_emissions", kwargs={"report_pk": not_my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_fetch_report_emissions(self):
        """
        Returns all emission sources for a report if user is manager
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        EmissionFactory.create(bilan=my_report)
        EmissionFactory.create(bilan=my_report)

        response = self.client.get(reverse("report_emissions", kwargs={"report_pk": my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 2)
        emission = body[0]
        self.assertIn("id", emission)
        # TODO: self.assertIn("resultat", emission)
        self.assertIn("note", emission)

    def test_unauthenticated_fetch_emission(self):
        """
        403 if attempt to fetch emission without logging in
        """
        response = self.client.get(reverse("emission", kwargs={"pk": 10}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_unauthorised_fetch_emission(self):
        """
        404 if attempt to fetch emission user doesn't manage
        """
        not_my_report = ReportFactory.create()
        emission = EmissionFactory.create(bilan=not_my_report)

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_fetch_emission(self):
        """
        Return emission given id
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(bilan=my_report)

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["id"], emission.id)
        self.assertIn("unite", body)
        # TODO: self.assertIn("resultat", body)

    @authenticate
    def test_update_emission(self):
        """
        Modify emission by id
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(bilan=my_report, unite="l")

        response = self.client.patch(reverse("emission", kwargs={"pk": emission.id}), {"unite": "ml"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["id"], emission.id)
        self.assertEqual(body["unite"], "ml")

    @authenticate
    def test_delete_emission(self):
        """
        Can delete emission by id
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(bilan=my_report)

        response = self.client.delete(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Emission.objects.count(), 0)
