from django.contrib.auth import get_user_model
from django.db import models
from data.emission_factors import get_emission_factors
from django.contrib.auth.models import AbstractUser
from data.insee_naf_division_choices import NafDivision
from data.region_choices import Region
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


class User(AbstractUser):
    ademe_id = models.CharField(verbose_name="identifiant ADEME", max_length=255, blank=True, null=True)


class Report(models.Model):
    class Meta:
        verbose_name = "bilan"
        verbose_name_plural = "bilans"
        constraints = [
            models.UniqueConstraint(fields=["siren", "annee"], name="annual_report"),
        ]

    class Status(models.TextChoices):
        DRAFT = "brouillon"
        PUBLISHED = "publié"

    class CalculationMode(models.TextChoices):
        MANUAL = "manuel"
        AUTO = "auto"

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)
    publication_date = models.DateTimeField(blank=True, null=True)
    statut = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)

    # TODO: double check that we shouldn't CASCADE on_delete
    gestionnaire = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True)

    # company fields
    raison_sociale = models.TextField(verbose_name="raison sociale")
    # TODO: validate min = 1 and max = 1000 (our scope: 50-500) ?
    nombre_salaries = models.IntegerField(verbose_name="nombre de salariés", blank=True, null=True)
    # TODO: add luhn validation
    siren = models.CharField(verbose_name="siren", max_length=9)
    region = models.CharField(
        verbose_name="région du siège", blank=True, null=True, choices=Region.choices, max_length=4
    )
    naf = models.CharField(
        verbose_name="code NAF (nomenclature d'activités française)",
        blank=True,
        null=True,
        choices=NafDivision.choices,
        max_length=4,
    )

    # validate year?
    annee = models.IntegerField(verbose_name="année")

    manuel_poste_1 = models.IntegerField(
        verbose_name="total poste 1 (manuel)",
        blank=True,
        null=True,
    )
    manuel_poste_2 = models.IntegerField(
        verbose_name="total poste 2 (manuel)",
        blank=True,
        null=True,
    )
    mode = models.CharField(max_length=10, choices=CalculationMode.choices, default=CalculationMode.AUTO)

    def sum_post(self, post):
        results = [
            emission.resultat for emission in Emission.objects.filter(poste=post, bilan=self) if emission.resultat
        ]
        if len(results):
            # don't rely on int rounding which rounds 0.5 to 0, use Decimal quantize instead
            return int(sum(results).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        else:
            return 0

    @property
    def poste_1(self):
        if self.mode == self.CalculationMode.MANUAL:
            return self.manuel_poste_1
        else:
            return self.sum_post(1)

    @property
    def poste_2(self):
        if self.mode == self.CalculationMode.MANUAL:
            return self.manuel_poste_2
        else:
            return self.sum_post(2)

    @property
    def total(self):
        if self.poste_1 is not None and self.poste_2 is not None:
            return self.poste_1 + self.poste_2
        elif self.poste_1 is not None:
            return self.poste_1
        elif self.poste_2 is not None:
            return self.poste_2
        else:
            return None

    def save(self, *args, **kwargs):
        if self.statut == self.Status.PUBLISHED:
            self.publication_date = timezone.now()
        super().save(*args, **kwargs)


class Emission(models.Model):
    class Meta:
        verbose_name = "emission"
        verbose_name_plural = "emissions"

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)

    bilan = models.ForeignKey(Report, on_delete=models.CASCADE)

    valeur = models.DecimalField(verbose_name="valeur", max_digits=10, decimal_places=2)  # max 99.999.999,99
    type = models.CharField(verbose_name="type d'emission", max_length=100)
    localisation = models.CharField(verbose_name="localisation", max_length=100, blank=True, null=True)
    unite = models.CharField(verbose_name="unité", max_length=20)
    poste = models.IntegerField(verbose_name="poste")
    note = models.TextField(verbose_name="note", blank=True, null=True)

    @property
    def resultat(self):
        factor = get_emission_factors().get_factor(self.type, self.unite, self.localisation)
        if factor:
            return Decimal(self.valeur * factor).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return None
