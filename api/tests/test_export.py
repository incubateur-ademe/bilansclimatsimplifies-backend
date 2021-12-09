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


class TestPrivateExport(APITestCase):
    @authenticate_staff
    def test_csv_export(self):
        """
        Test that private endpoint returns csv file of data
        """
        alice = UserFactory(first_name="Alice", last_name="Smith", email="alice@example.com")
        bob = UserFactory(first_name="Bob")
        ReportFactory(
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
        ReportFactory(gestionnaire=alice, annee=2021)
        ReportFactory(gestionnaire=bob, annee=2020)

        response = self.client.get(reverse("private-csv-export"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        # will just be copying logic here if test the full filename with date
        self.assertTrue(response["Content-Disposition"].startswith("attachment; filename=bilans_climat_simplifies_"))
        body = response.content.decode("utf-8").splitlines()
        self.assertEqual(len(body), 4)
        self.assertEqual(
            body[0],
            "siren,annee,raison_sociale,region,naf,nombre_salaries,mode,poste_1_tCO2e,poste_2_tCO2e,total_tCO2e,statut,creation_date,publication_date,gestionnaire.email,gestionnaire.prenom,gestionnaire.nom",
        )
        self.assertTrue(body[1].startswith("515277358,2020,Alice's Company,01,03,50,manuel,100,200,300,publié,"))
        self.assertTrue(body[1].endswith(",alice@example.com,Alice,Smith"))

    @authenticate
    def test_non_staff_rejected(self):
        """
        Test that non-staff users are rejected
        """
        response = self.client.get(reverse("private-csv-export"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_rejected(self):
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
        alice = UserFactory(first_name="Alice", last_name="Smith", email="alice@example.com")
        ReportFactory(
            gestionnaire=alice,
            siren="515277358",
            statut=Report.Status.PUBLISHED,
        )
        ReportFactory(statut=Report.Status.PUBLISHED, siren="794690446")
        ReportFactory(siren="910546308", statut=Report.Status.DRAFT)
        post_mocker = request_mock.post("http://example.com/dataset", json={"success": True})
        update_public_export()
        self.assertTrue(post_mocker.called_once)
        self.assertTrue(post_mocker.last_request.headers["x-api-key"] == "asecurekey")
        self.assertTrue(post_mocker.last_request.headers["content-type"].startswith("multipart/form-data; boundary="))
        print(post_mocker.last_request.text)
        self.assertTrue(
            "siren,annee,raison_sociale,region,naf,nombre_salaries,publication_date,poste_1_tCO2e,poste_2_tCO2e,total_tCO2e"
            in post_mocker.last_request.text
        )
        self.assertTrue("515277358" in post_mocker.last_request.text)
        self.assertTrue("794690446" in post_mocker.last_request.text)
        self.assertFalse("910546308" in post_mocker.last_request.text)
        self.assertFalse("alice@example.com" in post_mocker.last_request.text)

    @requests_mock.Mocker()
    @override_settings(KOUMOUL_API_URL="http://example.com/dataset")
    def test_no_published_reports(self, request_mock):
        """
        Test that the helper function does not call the external endpoint when there are no
        published reports (since this results in error in the external API)
        """
        ReportFactory(siren="910546308", statut=Report.Status.DRAFT)
        post_mocker = request_mock.post("http://example.com/dataset", json={"success": True})
        update_public_export()
        self.assertFalse(post_mocker.called)
