from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from data.models import User, Report, Emission


@admin.register(User)
class BcsUserAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "ademe_id",
        "date_joined",
    )
    search_fields = (
        "first_name",
        "last_name",
        "email",
    )
    readonly_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "date_joined",
        "last_login",
        "ademe_id",
        "is_superuser",
    )

    fieldsets = (
        (None, {"fields": ("username", "ademe_id", "first_name", "last_name", "email")}),
        (
            _("Autorisation"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("siren", "annee", "raison_sociale", "gestionnaire", "statut", "creation_date", "region", "naf")
    search_fields = ("raison_sociale", "siren")
    list_filter = ("annee", "statut", "region", "naf")
    readonly_fields = (
        "siren",
        "annee",
        "raison_sociale",
        "gestionnaire",
        "region",
        "naf",
        "statut",
        "creation_date",
        "publication_date",
        "mode",
        "manuel_poste_1",
        "manuel_poste_2",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "siren",
                    "annee",
                    "raison_sociale",
                    "gestionnaire",
                    "region",
                    "naf",
                    "statut",
                    "creation_date",
                    "publication_date",
                    "mode",
                    "manuel_poste_1",
                    "manuel_poste_2",
                )
            },
        ),
    )


@admin.register(Emission)
class EmissionAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "bilan",
        "poste",
        "valeur",
        "unite",
        "localisation",
        "creation_date",
    )
    search_fields = ("type",)
    readonly_fields = (
        "bilan",
        "type",
        "poste",
        "valeur",
        "unite",
        "creation_date",
        "localisation",
        "note",
    )

    fieldsets = ((None, {"fields": ("type", "poste", "valeur", "unite", "localisation", "note")}),)
