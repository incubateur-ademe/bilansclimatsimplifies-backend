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

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
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

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_unauthorised_fetch_report_emissions(self):
        """
        403 if not manager of the report
        """
        not_my_report = ReportFactory.create()
        EmissionFactory.create(bilan=not_my_report)
        EmissionFactory.create(bilan=not_my_report)

        response = self.client.get(reverse("report_emissions", kwargs={"report_pk": not_my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    # TODO: fetch specific emission by id
    # TODO: unauthed

    # TODO: update emission by id
    # TODO: unauthed

    # TODO: delete emission from report
    # TODO: check unauthenticated view & incorrect user view
