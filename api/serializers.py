from django.contrib.auth import get_user_model
from rest_framework import serializers
from data.models import Report, Emission


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["username", "email", "first_name", "last_name", "is_staff"]
        read_only_fields = fields


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
            "poste_1",
            "poste_2",
            "total",
            "mode",
            "creation_date",
            "publication_date",
            "gestionnaire",
        ]
        read_only_fields = fields


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
            "poste_1",
            "poste_2",
            "total",
        ]
        read_only_fields = fields


class EmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emission
        fields = ["id", "bilan", "poste", "type", "valeur", "unite", "note", "resultat"]
        read_only_fields = ["id", "resultat"]
