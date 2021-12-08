import factory
from factory import fuzzy
from django.contrib.auth import get_user_model
from .models import Report, Emission
from data.insee_naf_division_choices import NafDivision
from data.region_choices import Region


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("user_name")
    email = factory.Faker("email")
    ademe_id = factory.Faker("ssn")


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    gestionnaire = factory.SubFactory(UserFactory)
    raison_sociale = factory.Faker("company")
    siren = factory.Faker("pystr", min_chars=9, max_chars=9)
    annee = factory.Faker("year")
    naf = fuzzy.FuzzyChoice(list(NafDivision))
    region = fuzzy.FuzzyChoice(list(Region))
    nombre_salaries = factory.Faker("random_int", min=1, max=500)


class EmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Emission

    bilan = factory.SubFactory(ReportFactory)
    # could improve by using more realisic values for poste, type, localisation, unite
    poste = factory.Faker("random_int", min=1, max=2)
    type = factory.Faker("pystr", min_chars=4, max_chars=10)
    localisation = factory.Faker("pystr", min_chars=4, max_chars=10)
    valeur = factory.Faker("random_int", min=1, max=1000)
    unite = factory.Faker("pystr", min_chars=1, max_chars=3)
    note = factory.Faker("text", max_nb_chars=20)
