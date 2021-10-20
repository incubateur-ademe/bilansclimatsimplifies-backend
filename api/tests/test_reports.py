from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import ReportFactory, UserFactory
from data.models import Report


class TestReportApi(APITestCase):
    def test_unauthenticated_create_report(self):
        """
        Should not be able to create a report if not logged in
        """
        self.assertEqual(len(Report.objects.all()), 0)

        response = self.client.post(reverse("reports"), {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Report.objects.all()), 0)

    @authenticate
    def test_authenticated_create_report(self):
        """
        Should be able to create report, returning the db id of the created report
        """
        self.assertEqual(len(Report.objects.all()), 0)

        payload = {
            "raisonSociale": "My company",
            "siren": "123456789",
            "nombreSalaries": 200,
            "annee": 2020,
        }
        response = self.client.post(reverse("reports"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # TODO: self.assertEqual(response.json()["id"], reports[0].id)
        reports = Report.objects.all()
        self.assertEqual(len(reports), 1)

    @authenticate
    def test_authenticated_create_duplicate_report(self):
        """
        If attempt to create a report with same siren+year as another, return 400
        """
        siren = "123456789"
        year = 2020
        ReportFactory.create(siren=siren, annee=year)

        payload = {
            "raisonSociale": "My company",
            "siren": siren,
            "nombreSalaries": 200,
            "annee": year,
        }
        response = self.client.post(reverse("reports"), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # TODO: check error message
        reports = Report.objects.all()
        self.assertEqual(len(reports), 1)

    def test_unauthenticated_fetch_reports(self):
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_authenticated_fetch_reports(self):
        ReportFactory.create(annee=2020, gestionnaire=authenticate.user)
        ReportFactory.create(annee=2019, gestionnaire=authenticate.user)
        ReportFactory.create(annee=2019, gestionnaire=UserFactory.create())

        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 2)
        self.assertIn("raisonSociale", body[0])
        self.assertIn("annee", body[0])
        self.assertIn("id", body[0])
        self.assertIn("siren", body[0])
        self.assertIn("naf", body[0])
        self.assertIn("region", body[0])
        # TODO:
        # self.assertIn("poste_1", body[0])
        # self.assertIn("poste_2", body[0])
        # self.assertIn("totale", body[0])

    # TODO: fetch details of report by id, with calculated totals
    # TODO: check unauthenticated view

    # TODO: test modify report
    # TODO: test unauthenticated + unauthorised modify report

    # TODO: manually add poste totals
    # TODO: unauthed
    # TODO: check get bilan id + scope for manually added total returns just the total, no sources
