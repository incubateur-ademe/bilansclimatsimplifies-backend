from data.models import Report
from .utils import authenticate, authenticate_staff
from rest_framework.test import APITestCase
from rest_framework import status
from data.factories import ReportFactory, UserFactory
from django.urls import reverse
from data.region_choices import Region
from data.insee_naf_division_choices import NafDivision


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
            "siren,annee,raison_sociale,region,naf,nombre_salaries,mode,poste_1,poste_2,total,statut,creation_date,publication_date,gestionnaire.email,gestionnaire.first_name,gestionnaire.last_name",
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
