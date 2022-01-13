from django.contrib.auth import get_user_model
from django.db import models
from data.emission_factors import get_emission_factors
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from data.insee_naf_division_choices import NafDivision
from data.region_choices import Region
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from .validators import validate_employee_count, validate_report_year


class User(AbstractUser):
    ademe_id = models.CharField(verbose_name="identifiant ADEME", max_length=255, blank=True, null=True)


def luhn_validation(code):
    """
    Performs length and Luhn validation
    (https://portal.hardis-group.com/pages/viewpage.action?pageId=120357227)
    """
    if len(code) != 9:
        raise ValidationError("9 caractères numériques sont attendus")
    odd_digits = [int(n) for n in code[-1::-2]]
    even_digits = [int(n) for n in code[-2::-2]]
    checksum = sum(odd_digits)
    for digit in even_digits:
        checksum += sum(int(n) for n in str(digit * 2))
    luhn_checksum_valid = checksum % 10 == 0

    if not luhn_checksum_valid:
        raise ValidationError("Le numéro SIREN n'est pas valide.")


# NB: parts of this model are used by the public export, take care when changing it.
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
        MANUAL = "manuel", "Déclaré"
        AUTO = "auto", "Calculé"

    creation_date = models.DateTimeField(auto_now_add=True, verbose_name="date de création")
    modification_date = models.DateTimeField(auto_now=True)
    publication_date = models.DateTimeField(blank=True, null=True, verbose_name="date de publication")
    statut = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, verbose_name="statut")

    # TODO: double check that we shouldn't CASCADE on_delete
    gestionnaire = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, blank=True, null=True, verbose_name="créateur du bilan"
    )

    # company fields
    raison_sociale = models.TextField(verbose_name="raison sociale")
    nombre_salaries = models.IntegerField(
        verbose_name="nombre de salariés",
        blank=True,
        null=True,
        validators=[validate_employee_count],
    )
    siren = models.CharField(verbose_name="SIREN", max_length=9, validators=[luhn_validation])
    region = models.CharField(verbose_name="code région", blank=True, null=True, choices=Region.choices, max_length=4)
    naf = models.CharField(
        verbose_name="code NAF",
        blank=True,
        null=True,
        choices=NafDivision.choices,
        max_length=4,
    )

    annee = models.IntegerField(
        verbose_name="année de reporting",
        validators=[validate_report_year],
    )

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
    mode = models.CharField(
        max_length=10,
        choices=CalculationMode.choices,
        default=CalculationMode.AUTO,
        verbose_name="mode de publication",
    )

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
    def poste_1_t(self):
        return kg_to_t(self.poste_1)

    @property
    def poste_2(self):
        if self.mode == self.CalculationMode.MANUAL:
            return self.manuel_poste_2
        else:
            return self.sum_post(2)

    @property
    def poste_2_t(self):
        return kg_to_t(self.poste_2)

    @property
    def total(self):
        if self.poste_1 is not None or self.poste_2 is not None:
            return (self.poste_1 or 0) + (self.poste_2 or 0)
        else:
            return None

    @property
    def total_t(self):
        return kg_to_t(self.total)

    def save(self, *args, **kwargs):
        if self.statut == self.Status.PUBLISHED:
            self.publication_date = timezone.now()
        super().save(*args, **kwargs)


def kg_to_t(value):
    return value / 1000 if value is not None else None


class Emission(models.Model):
    class Meta:
        verbose_name = "emission"
        verbose_name_plural = "emissions"

    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)

    bilan = models.ForeignKey(Report, on_delete=models.CASCADE)

    valeur = models.DecimalField(verbose_name="valeur", max_digits=10, decimal_places=2)  # max 99.999.999,99
    type = models.CharField(verbose_name="type d'émission", max_length=100)
    localisation = models.CharField(verbose_name="localisation", max_length=100, blank=True, null=True)
    unite = models.CharField(verbose_name="unité", max_length=20)
    poste = models.IntegerField(verbose_name="poste")
    note = models.TextField(verbose_name="note", blank=True, null=True)

    @property
    def resultat(self):
        factor = self.facteur_d_emission
        if factor:
            return Decimal(self.valeur * factor).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return None

    @property
    def facteur_d_emission(self):
        return get_emission_factors().get_factor(self.type, self.unite, self.localisation)

    @property
    def classification(self):
        return get_emission_factors().get_classification(self.type)
