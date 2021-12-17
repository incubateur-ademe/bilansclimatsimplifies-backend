from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_value_gte(value, lower_limit):
    if value < lower_limit:
        raise ValidationError(f"{value} est moins que {lower_limit}", params={"value": value})


def validate_value_lte(value, upper_limit):
    if value > upper_limit:
        raise ValidationError(f"{value} est plus que {upper_limit}", params={"value": value})


def validate_employee_count(value):
    validate_value_gte(value, 50)
    validate_value_lte(value, 500)


def validate_report_year(value):
    validate_value_gte(value, timezone.now().year - 2)
    validate_value_lte(value, timezone.now().year)
