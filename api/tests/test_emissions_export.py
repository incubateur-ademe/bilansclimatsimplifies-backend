from .utils import authenticate
from rest_framework.test import APITestCase
from rest_framework import status
from data.factories import ReportFactory, EmissionFactory
from django.urls import reverse
from data.emission_factors import get_emission_factors
from unittest.mock import patch

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
class TestPrivateReportExport(APITestCase):
    @authenticate
    def test_csv_emissions_export(self):
        """
        Test that private endpoint returns csv file of data
        """
        report = ReportFactory.create(gestionnaire=authenticate.user, annee=2020, siren="123456789")
        emissions = [
            EmissionFactory.create(
                bilan=report,
                type="Gaz naturel",
                valeur=10,
                unite="GJ PCI",
                localisation="Guadeloupe, Martinique, Guyane, Corse",
                note="Note pour gaz naturel",
                poste="1",
            ),
            EmissionFactory.create(
                bilan=report,
                type="Essence, E10",
                valeur=1000,
                unite="kg",
                localisation="France continentale",
                note="Note pour Essence, E10",
                poste="2",
            ),
            EmissionFactory.create(
                bilan=report,
                type="Essence, E10",
                valeur=1000,
                unite="kg",
                localisation="Guadeloupe, Martinique, Guyane, Corse",
                note="2eme emission pour Essence, E10",
                poste="2",
            ),
        ]
        EmissionFactory.create(valeur=1234)

        response = self.client.get(reverse("emissions-csv-export", kwargs={"report_pk": report.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertTrue(response["Content-Disposition"].startswith("attachment; filename=export_123456789_2020.csv"))

        body = response.content.decode("utf-8")
        self.assertEqual(body.find("1234"), -1)  # assert only emissions for current report in csv
        body = body.splitlines()
        self.assertEqual(len(body), 4)
        self.assertEqual(
            body[0],
            "type,valeur,unite,facteur_d_emission,resultat_kgCO2e,poste,localisation,note",
        )
        self.assertEqual(
            body[1],
            f'Gaz naturel,10.00,GJ PCI,2,{emissions[0].resultat},1,"Guadeloupe, Martinique, Guyane, Corse",Note pour gaz naturel',
        )
        self.assertEqual(
            body[2],
            f'"Essence, E10",1000.00,kg,0.1,{emissions[1].resultat},2,France continentale,"Note pour Essence, E10"',
        )
        self.assertEqual(
            body[3],
            f'"Essence, E10",1000.00,kg,0.2,{emissions[2].resultat},2,"Guadeloupe, Martinique, Guyane, Corse","2eme emission pour Essence, E10"',
        )

    def test_unauthenticated_user_rejected_emissions_export(self):
        """
        Test that unauthenticated users are rejected
        """
        response = self.client.get(reverse("emissions-csv-export", kwargs={"report_pk": 0}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @authenticate
    def test_cannot_export_other_report(self):
        """
        Test that user can only export reports they manage
        """
        report = ReportFactory.create()

        response = self.client.get(reverse("emissions-csv-export", kwargs={"report_pk": report.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
