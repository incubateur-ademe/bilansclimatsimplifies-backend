from django.contrib.auth import get_user_model
from django.db import models


class Report(models.Model):
    class Meta:
        verbose_name = "bilan"
        verbose_name_plural = "bilans"
        constraints = [
            models.UniqueConstraint(fields=["siren", "annee"], name="annual_report"),
        ]

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)

    # TODO: double check that we shouldn't CASCADE on_delete
    gestionnaire = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True)

    # company fields
    raison_sociale = models.TextField(verbose_name="raison sociale")
    # TODO: consider writing a validator for min = 0 max = 1000 (our scope: 50-500)
    nombre_salaries = models.IntegerField(verbose_name="nombre de salariés", blank=True, null=True)
    siren = models.CharField(verbose_name="siren", max_length=9)
    # TODO: maybe make this choices
    region = models.CharField(verbose_name="région du siège", blank=True, null=True, max_length=40)
    naf = models.CharField(
        verbose_name="code NAF (nomenclature d'activités française)", blank=True, null=True, max_length=20
    )

    annee = models.IntegerField(verbose_name="année")

    # TODO: calculated totals


class Emission(models.Model):
    class Meta:
        verbose_name = "emission"
        verbose_name_plural = "emissions"

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)

    bilan = models.ForeignKey(Report, on_delete=models.CASCADE)

    valeur = models.DecimalField(verbose_name="valeur", max_digits=10, decimal_places=2)  # max 99.999.999,99
    type = models.CharField(verbose_name="type d'emission", max_length=20)
    unite = models.CharField(verbose_name="unité", max_length=10)
    poste = models.IntegerField(verbose_name="poste")
    note = models.TextField(verbose_name="note", blank=True, null=True)

    # TODO: calculated resultat
