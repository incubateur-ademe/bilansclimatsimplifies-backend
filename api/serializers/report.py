from rest_framework import serializers
from data.models import Report
from rest_framework.validators import UniqueTogetherValidator


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
        validators = [
            UniqueTogetherValidator(
                queryset=Report.objects.all(),
                fields=["siren", "annee"],
                message="Un bilan avec ce couple SIREN / Année de reporting existe déjà.",
            )
        ]
