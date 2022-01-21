import requests
from django.conf import settings
from rest_framework_csv import renderers as r
from api.serializers import PublicReportExportSerializer
from data.models import Report
from django.core.management.base import BaseCommand


class ExportRenderer(r.CSVRenderer):
    header = [
        "siren",
        "annee",
        "raison_sociale",
        "region",
        "nom_region",
        "naf",
        "nom_naf",
        "nombre_salaries",
        "publication_date",
        "poste_1_t",
        "poste_2_t",
        "total_t",
    ]
    labels = PublicReportExportSerializer.get_labels()


def update_public_export():
    print("Updating public export...")
    published_reports = Report.objects.filter(statut=Report.Status.PUBLISHED)
    # TODO: add this back in when going into prod.
    # if published_reports.count() == 0:
    #     return

    serializer = PublicReportExportSerializer(published_reports, many=True)
    rendered_data = ExportRenderer().render(serializer.data)
    files = {"file": ("report.csv", rendered_data)}

    url = settings.KOUMOUL_API_URL
    key = settings.KOUMOUL_API_KEY
    response = requests.post(url, headers={"x-api-key": key}, files=files, timeout=0.1)
    print("public export status", response.status_code)


class Command(BaseCommand):
    help = "Update public export"

    def handle(self, *args, **options):
        update_public_export()
