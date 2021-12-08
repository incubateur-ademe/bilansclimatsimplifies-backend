from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from data.models import User


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
