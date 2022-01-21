from data.models import Report
from .utils import authenticate, authenticate_staff
from rest_framework.test import APITestCase
from rest_framework import status
from data.factories import ReportFactory, UserFactory
from django.urls import reverse

from django.test.utils import override_settings
from data.region_choices import Region
from data.insee_naf_division_choices import NafDivision

import requests_mock
from api.management.commands.publicexport import update_public_export


class TestPrivateReportExport(APITestCase):
    @authenticate_staff
    def test_csv_report_export(self):
        """
        Test that private endpoint returns csv file of data
        """
        alice = UserFactory.create(first_name="Alice", last_name="Smith", email="alice@example.com")
        bob = UserFactory.create(first_name="Bob")
        ReportFactory.create(
            gestionnaire=alice,
            annee=2020,
            siren="515277358",
            raison_sociale="Alice's Company",
            region=Region.guadeloupe,
            naf=NafDivision.aquaculture,
            statut=Report.Status.PUBLISHED,
            mode=Report.CalculationMode.MANUAL,
            manuel_poste_1=100,
            manuel_poste_2=200,
            nombre_salaries=50,
        )
        ReportFactory.create(gestionnaire=alice, annee=2021)
        ReportFactory.create(gestionnaire=bob, annee=2020)

        response = self.client.get(reverse("private-csv-export"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        # will just be copying logic here if test the full filename with date
        self.assertTrue(response["Content-Disposition"].startswith("attachment; filename=bilans_climat_simplifies_"))
        body = response.content.decode("utf-8").splitlines()
        self.assertEqual(len(body), 4)
        self.assertEqual(
            body[0],
            "SIREN,Année de reporting,Raison sociale,Code région,Nom région,Code NAF,Division NAF,Nombre de salariés,Mode de publication,Poste 1 tCO2e,Poste 2 tCO2e,Total tCO2e,Statut,Date de création,Date de publication,Email du créateur du bilan,Prénom du créateur du bilan,Nom du créateur du bilan",
        )
        self.assertTrue(
            body[1].startswith(
                "515277358,2020,Alice's Company,01,Guadeloupe,03,Pêche et aquaculture,50,Déclaré,0.1,0.2,0.3,publié,"
            )
        )
        self.assertTrue(body[1].endswith(",alice@example.com,Alice,Smith"))

    @authenticate_staff
    def test_xlsx_export(self):
        """
        Test that private endpoint returns xlsx file of data
        """
        ReportFactory.create(annee=2020)
        ReportFactory.create(annee=2021)
        response = self.client.get(reverse("private-xlsx-export"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/xlsx; charset=utf-8")
        self.assertTrue(response["Content-Disposition"].startswith("attachment; filename=bilans_climat_simplifies_"))

    @authenticate
    def test_only_staff_access_xlsx_export(self):
        """
        Test that private endpoint returns xlsx file of data
        """
        response = self.client.get(reverse("private-xlsx-export"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @authenticate
    def test_only_staff_access_report_export(self):
        """
        Test that non-staff users are rejected
        """
        response = self.client.get(reverse("private-csv-export"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_rejected_report_export(self):
        """
        Test that unauthenticated users are rejected
        """
        response = self.client.get(reverse("private-csv-export"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPublicExport(APITestCase):
    @requests_mock.Mocker()
    @override_settings(KOUMOUL_API_KEY="asecurekey")
    @override_settings(KOUMOUL_API_URL="http://example.com/dataset")
    def test_external_api_call(self, request_mock):
        """
        Test that the helper function calls the external endpoint as expected
        with the right data
        """
        alice = UserFactory.create(first_name="Alice", last_name="Smith", email="alice@example.com")
        ReportFactory.create(
            gestionnaire=alice,
            siren="515277358",
            statut=Report.Status.PUBLISHED,
        )
        ReportFactory.create(statut=Report.Status.PUBLISHED, siren="794690446")
        ReportFactory.create(siren="910546308", statut=Report.Status.DRAFT)
        post_mocker = request_mock.post("http://example.com/dataset", json={"success": True})
        update_public_export()
        self.assertTrue(post_mocker.called_once)
        self.assertTrue(post_mocker.last_request.headers["x-api-key"] == "asecurekey")
        self.assertTrue(post_mocker.last_request.headers["content-type"].startswith("multipart/form-data; boundary="))
        self.assertTrue(
            "SIREN,Année de reporting,Raison sociale,Code région,Nom région,Code NAF,Division NAF,Nombre de salariés,Date de publication,Poste 1 tCO2e,Poste 2 tCO2e,Total tCO2e"
            in post_mocker.last_request.text
        )
        self.assertTrue("515277358" in post_mocker.last_request.text)
        self.assertTrue("794690446" in post_mocker.last_request.text)
        self.assertFalse("910546308" in post_mocker.last_request.text)
        self.assertFalse("alice@example.com" in post_mocker.last_request.text)

    # TODO: add back in
    # @requests_mock.Mocker()
    # @override_settings(KOUMOUL_API_URL="http://example.com/dataset")
    # def test_no_published_reports(self, request_mock):
    #     """
    #     Test that the helper function does not call the external endpoint when there are no
    #     published reports (since this results in error in the external API)
    #     """
    #     ReportFactory.create(siren="910546308", statut=Report.Status.DRAFT)
    #     post_mocker = request_mock.post("http://example.com/dataset", json={"success": True})
    #     update_public_export()
    #     self.assertFalse(post_mocker.called)
