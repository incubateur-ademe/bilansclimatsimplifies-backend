import json
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
import requests
from django.conf import settings
from rest_framework_csv import renderers as r
from api.serializers import PublicReportExportSerializer
from data.models import Report


def camelize(data):
    camel_case_bytes = CamelCaseJSONRenderer().render(data)
    return json.loads(camel_case_bytes.decode("utf-8"))


class ExportRenderer(r.CSVRenderer):
    header = [
        "siren",
        "annee",
        "raison_sociale",
        "region",
        "naf",
        "nombre_salaries",
        "poste_1",
        "poste_2",
        "total",
    ]
    labels = {
        "poste_1": "poste_1_tCO2e",
        "poste_2": "poste_2_tCO2e",
        "total": "total_tCO2e",
    }


def update_public_export():
    published_reports = Report.objects.filter(statut=Report.Status.PUBLISHED)
    if published_reports.count() == 0:
        return

    serializer = PublicReportExportSerializer(published_reports, many=True)
    rendered_data = ExportRenderer().render(serializer.data)
    files = {"file": ("report.csv", rendered_data)}

    url = settings.KOUMOUL_API_URL
    key = settings.KOUMOUL_API_KEY
    requests.post(url, headers={"x-api-key": key}, files=files)
