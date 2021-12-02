from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import EmissionFactory, ReportFactory, UserFactory
from data.models import Report
from decimal import Decimal
from data.emission_factors import get_emission_factors
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta


class TestReportApi(APITestCase):
    def test_unauthenticated_create_report(self):
        """
        Should not be able to create a report if not logged in
        """
        self.assertEqual(len(Report.objects.all()), 0)

        response = self.client.post(reverse("reports"), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
        self.assertIn("total", body[0])

    def test_unauthenticated_fetch_report(self):
        """
        403 if attempt to fetch report without logging in
        """
        response = self.client.get(reverse("report", kwargs={"pk": 10}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_unauthorised_fetch_report(self):
        """
        404 if attempt to fetch report user doesn't manage
        """
        not_my_report = ReportFactory.create()

        response = self.client.get(reverse("report", kwargs={"pk": not_my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @authenticate
    def test_fetch_report(self):
        """
        Return report given id
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        response = self.client.get(reverse("report", kwargs={"pk": my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["id"], my_report.id)
        self.assertIn("annee", body)
        self.assertIn("poste1", body)
        self.assertIn("poste2", body)
        self.assertIn("total", body)

    @authenticate
    def test_update_report(self):
        """
        Modify report by id
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user, nombre_salaries=60)

        response = self.client.patch(reverse("report", kwargs={"pk": my_report.id}), {"nombreSalaries": 100})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["id"], my_report.id)
        self.assertEqual(body["nombreSalaries"], 100)

    @authenticate
    def test_publish_report(self):
        """
        Can publish report and automatically set publication date
        NB: if there are further edits, publication date is updated with the latest edit date
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        self.assertEqual(my_report.statut, Report.Status.DRAFT)
        self.assertEqual(my_report.publication_date, None)

        response = self.client.patch(reverse("report", kwargs={"pk": my_report.id}), {"statut": "publié"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        my_report.refresh_from_db()
        self.assertEqual(my_report.statut, Report.Status.PUBLISHED)
        self.assertTrue(timezone.now() - my_report.publication_date < timedelta(days=1))

    example_emission_factors = {
        "Gaz naturel": {
            "facteurs": {
                "France continentale": {
                    "kgCO2e/GJ PCI": "0.5",
                },
                "Guadeloupe, Martinique, Guyane, Corse": {
                    "kgCO2e/GJ PCI": "2",
                },
            },
        },
        "Essence, E10": {
            "facteurs": {
                "France continentale": {
                    "kgCO2e/kg": "0.1",
                },
                "Guadeloupe, Martinique, Guyane, Corse": {
                    "kgCO2e/kg": "0.2",
                },
            },
        },
    }

    @patch.object(get_emission_factors(), "emission_factors", example_emission_factors)
    @authenticate
    def test_report_totals(self):
        """
        Return totals for each poste and sum of postes
        # TODO: test decimal arithmetic
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        EmissionFactory.create(
            bilan=my_report, valeur=10, type="Gaz naturel", unite="GJ PCI", localisation="France continentale", poste=1
        )
        EmissionFactory.create(
            bilan=my_report,
            valeur=10,
            type="Gaz naturel",
            unite="GJ PCI",
            localisation="Guadeloupe, Martinique, Guyane, Corse",
            poste=1,
        )
        EmissionFactory.create(
            bilan=my_report, valeur=10, type="Essence, E10", unite="kg", localisation="France continentale", poste=2
        )
        EmissionFactory.create(
            bilan=my_report,
            valeur=10,
            type="Essence, E10",
            unite="kg",
            localisation="Guadeloupe, Martinique, Guyane, Corse",
            poste=2,
        )

        response = self.client.get(reverse("report", kwargs={"pk": my_report.id}))
        self.assertEqual(my_report.poste_1, Decimal("25"))
        self.assertEqual(my_report.poste_2, Decimal("3"))
        self.assertEqual(my_report.total, Decimal("28"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["poste1"], 25)
        self.assertEqual(body["poste2"], 3)
        self.assertEqual(body["total"], 28)

    @authenticate
    def test_delete_report(self):
        """
        Can delete report
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        response = self.client.delete(reverse("report", kwargs={"pk": my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Report.objects.count(), 0)

    @authenticate
    def test_manually_added_post_totals(self):
        """
        Can choose to add a manual total, and recieve this total instead of the calculated one
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        EmissionFactory.create(bilan=my_report, poste=1, valeur=10, type="Anthracite", unite="kg")
        EmissionFactory.create(bilan=my_report, poste=2, valeur=10, type="Articulé", unite="t.km")
        self.assertNotEqual(my_report.poste_1, Decimal("300"))
        self.assertNotEqual(my_report.poste_2, Decimal("100"))
        self.assertNotEqual(my_report.total, Decimal("400"))

        response = self.client.patch(
            reverse("report", kwargs={"pk": my_report.id}),
            {"manuelPoste1": 300, "manuelPoste2": 100, "mode": "manuel"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["poste1"], 300)
        self.assertEqual(body["poste2"], 100)
        self.assertEqual(body["total"], 400)  # TODO: test decimal arithmetic
        self.assertEqual(body["mode"], "manuel")

    @authenticate
    def test_revert_to_automatic_calculations(self):
        """
        Can choose to switch back to automatic calculations after setting manual totals
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        EmissionFactory.create(bilan=my_report, poste=1, valeur=10, type="Anthracite", unite="kg")
        EmissionFactory.create(bilan=my_report, poste=2, valeur=10, type="Articulé", unite="t.km")
        self.assertNotEqual(my_report.poste_1, Decimal("300"))
        self.assertNotEqual(my_report.poste_2, Decimal("100"))
        self.assertNotEqual(my_report.total, Decimal("400"))

        self.client.patch(
            reverse("report", kwargs={"pk": my_report.id}),
            {"manuelPoste1": 300, "manuelPoste2": 100, "mode": "manuel"},
        )
        response = self.client.patch(
            reverse("report", kwargs={"pk": my_report.id}),
            {"mode": "auto"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertNotEqual(body["poste1"], 300)
        self.assertNotEqual(body["poste2"], 100)
        self.assertNotEqual(body["total"], 400)
        self.assertEqual(body["mode"], "auto")

    @authenticate
    def test_manual_mode_no_totals(self):
        """
        If switch to manual mode without adding post totals, recieve undefined
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        EmissionFactory.create(bilan=my_report, poste=1, valeur=10, type="Anthracite", unite="kg")
        EmissionFactory.create(bilan=my_report, poste=2, valeur=10, type="Articulé", unite="t.km")
        self.assertIsNotNone(my_report.poste_1)
        self.assertIsNotNone(my_report.poste_2)
        self.assertIsNotNone(my_report.total)

        response = self.client.patch(
            reverse("report", kwargs={"pk": my_report.id}),
            {"mode": "manuel"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIsNone(body["poste1"])
        self.assertIsNone(body["poste2"])
        self.assertIsNone(body["total"])
        self.assertEqual(body["mode"], "manuel")
