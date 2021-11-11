from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import EmissionFactory, ReportFactory, UserFactory
from data.models import Report


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
        Can publish report
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        self.assertEqual(my_report.statut, Report.Status.DRAFT)

        response = self.client.patch(reverse("report", kwargs={"pk": my_report.id}), {"statut": "publié"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        my_report.refresh_from_db()
        self.assertEqual(my_report.statut, Report.Status.PUBLISHED)

    @authenticate
    def test_report_totals(self):
        """
        Return totals for each poste and sum of postes
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        EmissionFactory.create(bilan=my_report, poste=1, valeur=5)
        EmissionFactory.create(bilan=my_report, poste=1, valeur=10)
        EmissionFactory.create(bilan=my_report, poste=2, valeur=15)
        EmissionFactory.create(bilan=my_report, poste=2, valeur=20)

        response = self.client.get(reverse("report", kwargs={"pk": my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["total"], my_report.total)
        self.assertEqual(body["poste1"], my_report.poste_1)
        self.assertEqual(body["poste2"], my_report.poste_2)
        self.assertEqual(my_report.total, 100)
        self.assertEqual(my_report.poste_1, 30)
        self.assertEqual(my_report.poste_2, 70)

    @authenticate
    def test_delete_report(self):
        """
        Can delete report
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        response = self.client.delete(reverse("report", kwargs={"pk": my_report.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Report.objects.count(), 0)

    # TODO: unauthed
    # TODO: check get bilan id + scope for manually added total returns just the total, no sources
