from django.contrib.auth import get_user_model
from rest_framework import serializers
from data.models import Report, Emission


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["username", "email", "first_name", "last_name", "is_staff"]
        read_only_fields = fields


def verbose_fieldname_dict(model):
    return {
        f.name: (f.verbose_name[0].upper() + f.verbose_name[1:]) for f in model._meta.fields + model._meta.many_to_many
    }


def verbose_report_fieldname_dict():
    labels = verbose_fieldname_dict(Report)
    # the following are computed properties that can't be given a verbose_name so have to be treated manually
    return {
        **labels,
        **{
            "poste_1_t": "Poste 1 tCO2e",
            "poste_2_t": "Poste 2 tCO2e",
            "total_t": "Total tCO2e",
        },
    }


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "siren",
            "raison_sociale",
            "naf",
            "nombre_salaries",
            "region",
            "annee",
            "statut",
            "poste_1",
            "poste_2",
            "total",
            "manuel_poste_1",
            "manuel_poste_2",
            "mode",
        ]


class PrivateReportExportSerializer(serializers.ModelSerializer):
    gestionnaire = UserSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            "siren",
            "raison_sociale",
            "naf",
            "nombre_salaries",
            "region",
            "annee",
            "statut",
            "poste_1_t",
            "poste_2_t",
            "total_t",
            "mode",
            "creation_date",
            "publication_date",
            "gestionnaire",
        ]
        read_only_fields = fields

    def get_labels():
        return verbose_report_fieldname_dict()


class PublicReportExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "siren",
            "raison_sociale",
            "naf",
            "nombre_salaries",
            "region",
            "annee",
            "poste_1_t",
            "poste_2_t",
            "total_t",
            "publication_date",
        ]
        read_only_fields = fields

    def get_labels():
        return verbose_report_fieldname_dict()


class EmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emission
        fields = ["id", "bilan", "poste", "type", "localisation", "valeur", "unite", "note", "resultat"]
        read_only_fields = ["id", "resultat"]


class EmissionExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emission
        fields = ["poste", "type", "localisation", "valeur", "unite", "note", "resultat", "facteur_d_emission"]

    def get_labels():
        return {
            **verbose_fieldname_dict(Emission),
            **{"resultat": "Résultat kgCO2e", "facteur_d_emission": "Facteur d'émission"},
        }
