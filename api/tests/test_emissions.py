from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .utils import authenticate
from data.factories import ReportFactory, EmissionFactory
from data.models import Emission
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
    "Essence, E85": {
        "facteurs": {
            "France continentale": {
                "kgCO2e/kg": "0.85",
            },
        },
    },
}


@patch.object(get_emission_factors(), "emission_factors", example_emission_factors)
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
        TODO: bad request if doesn't fit in emissions file?
        """
        self.assertEqual(len(Emission.objects.all()), 0)
        my_report = ReportFactory.create(gestionnaire=authenticate.user)

        payload = {
            "bilan": my_report.id,
            "type": "Essence, E10",
            "localisation": "Guadeloupe, Martinique, Guyane, Corse",
            "valeur": 100,
            "unite": "l",
            "poste": 1,
            "note": "Utilisé par le client",
        }
        response = self.client.post(reverse("emissions"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        emissions = Emission.objects.all()
        self.assertEqual(len(emissions), 1)
        emission = emissions[0]
        self.assertEqual(emission.bilan, my_report)
        self.assertEqual(emission.type, "Essence, E10")
        self.assertEqual(emission.localisation, "Guadeloupe, Martinique, Guyane, Corse")
        self.assertEqual(emission.valeur, 100)
        self.assertEqual(emission.unite, "l")
        self.assertEqual(emission.poste, 1)
        self.assertEqual(emission.note, "Utilisé par le client")
        body = response.json()
        self.assertEqual(body["id"], emissions[0].id)
        self.assertIn("resultat", body)

    def test_unauthenticated_fetch_report_emissions(self):
        """
        401 if not logged in
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
        self.assertIn("resultat", emission)
        self.assertIn("note", emission)

    def test_unauthenticated_fetch_emission(self):
        """
        401 if attempt to fetch emission without logging in
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
        self.assertIn("resultat", body)

    @authenticate
    def test_update_emission(self):
        """
        Modify emission by id
        TODO: reject modification that doesn't fit in emissions file?
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(bilan=my_report, unite="l")

        response = self.client.patch(reverse("emission", kwargs={"pk": emission.id}), {"unite": "ml"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["id"], emission.id)
        self.assertEqual(body["unite"], "ml")

    @authenticate
    def test_cannot_modify_emission_result(self):
        """
        Cannot modify emission result
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(bilan=my_report, valeur=10)
        old_emission_result = emission.resultat
        self.assertNotEqual(old_emission_result, 100)

        response = self.client.patch(reverse("emission", kwargs={"pk": emission.id}), {"resultat": 100})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emission.refresh_from_db()
        self.assertEqual(emission.resultat, old_emission_result)

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

    @authenticate
    def test_emission_result_calculation(self):
        """
        Test that emission result is calculated correctly
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(
            bilan=my_report,
            type="Essence, E10",
            valeur=1000,
            unite="kg",
            localisation="France continentale",
        )

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["resultat"], 100.0)

    @authenticate
    def test_fetch_emission_without_location_one_option(self):
        """
        If an emission is saved without a location, and there is only one choice in
        the file for factors, use that choice
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(
            bilan=my_report, type="Essence, E85", valeur=1000, unite="kg", localisation=None
        )

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["resultat"], 850.0)

    @authenticate
    def test_fetch_emission_without_location_multiple_options(self):
        """
        If an emission is saved without a location, and there are multiple choices, return null
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(
            bilan=my_report, type="Essence, E10", valeur=1000, unite="kg", localisation=None
        )

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["resultat"], None)

    @authenticate
    def test_round_result_1_sig_fig(self):
        """
        Test that result is rounded to 1 sig fig
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(
            bilan=my_report, type="Essence, E85", valeur=1, unite="kg", localisation=None
        )

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["resultat"], 0.9)

    # what is expected behaviour if no emission factor to calculate result?


class TestEmissionApiRealFactors(APITestCase):
    @authenticate
    def test_result_generated(self):
        """
        Test that some result is generated. Smoke test to check that dummy file format
        reflects real file format.
        """
        my_report = ReportFactory.create(gestionnaire=authenticate.user)
        emission = EmissionFactory.create(
            bilan=my_report,
            type="Essence, E10",
            valeur=1000,
            unite="kg",
            localisation="France continentale",
        )

        response = self.client.get(reverse("emission", kwargs={"pk": emission.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        # actual calculations tested with unit tests above
        self.assertIsNotNone(body["resultat"])
        self.assertTrue(body["resultat"] > 0)
