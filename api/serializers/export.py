from rest_framework import serializers
from data.insee_naf_division_choices import NafDivision
from data.models import Report, Emission
from data.region_choices import Region


# TODO: see if can check serializer label as well to avoid repetition of names between CSV and XLSX export types
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


class PrivateReportExportSerializer(serializers.ModelSerializer):
    nom_naf = serializers.CharField(source="naf", label="Division NAF")
    nom_region = serializers.CharField(source="region", label="Nom région")
    raison_sociale = serializers.ReadOnlyField(label="Raison sociale")
    statut = serializers.ReadOnlyField(label="Statut")
    poste_1_t = serializers.ReadOnlyField(label="Poste 1 tCO2e")
    poste_2_t = serializers.ReadOnlyField(label="Poste 2 tCO2e")
    total_t = serializers.ReadOnlyField(label="Total tCO2e")
    gestionnaire_email = serializers.ReadOnlyField(source="gestionnaire.email", label="Email du créateur du bilan")
    gestionnaire_first_name = serializers.ReadOnlyField(
        source="gestionnaire.first_name", label="Prénom du créateur du bilan"
    )
    gestionnaire_last_name = serializers.ReadOnlyField(
        source="gestionnaire.last_name", label="Nom du créateur du bilan"
    )

    class Meta:
        model = Report
        fields = [
            "siren",
            "annee",
            "raison_sociale",
            "region",
            "nom_region",
            "naf",
            "nom_naf",
            "nombre_salaries",
            "mode",
            "poste_1_t",
            "poste_2_t",
            "total_t",
            "statut",
            "creation_date",
            "publication_date",
            "gestionnaire_email",
            "gestionnaire_first_name",
            "gestionnaire_last_name",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["nom_naf"] = NafDivision(ret["nom_naf"]).label
        ret["nom_region"] = Region(ret["nom_region"]).label
        ret["mode"] = Report.CalculationMode(ret["mode"]).label
        return ret

    def get_labels():
        return {**verbose_report_fieldname_dict(), **{"nom_naf": "Division NAF", "nom_region": "Nom région"}}


class PublicReportExportSerializer(serializers.ModelSerializer):
    nom_naf = serializers.CharField(source="naf", read_only=True)
    nom_region = serializers.CharField(source="region", read_only=True)

    class Meta:
        model = Report
        fields = [
            "siren",
            "raison_sociale",
            "naf",
            "nom_naf",
            "nombre_salaries",
            "region",
            "nom_region",
            "annee",
            "poste_1_t",
            "poste_2_t",
            "total_t",
            "publication_date",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["nom_naf"] = NafDivision(ret["nom_naf"]).label
        ret["nom_region"] = Region(ret["nom_region"]).label
        return ret

    def get_labels():
        return {**verbose_report_fieldname_dict(), **{"nom_naf": "Division NAF", "nom_region": "Nom région"}}


class EmissionExportSerializer(serializers.ModelSerializer):
    poste = serializers.ReadOnlyField(label="Poste")
    valeur = serializers.ReadOnlyField(label="Valeur")
    note = serializers.ReadOnlyField(label="Note")
    localisation = serializers.ReadOnlyField(label="Localisation")
    resultat = serializers.ReadOnlyField(label="Résultat kgCO2e")
    facteur_d_emission = serializers.ReadOnlyField(label="Facteur d'émission")

    class Meta:
        model = Emission
        fields = ["type", "valeur", "unite", "facteur_d_emission", "resultat", "poste", "localisation", "note"]

    def get_labels():
        return {
            **verbose_fieldname_dict(Emission),
            **{"resultat": "Résultat kgCO2e", "facteur_d_emission": "Facteur d'émission"},
        }
