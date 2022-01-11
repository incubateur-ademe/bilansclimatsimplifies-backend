from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from api.views import AdemeUserView, CreateAccountView
from api.views import ReportsView, ReportView
from api.views import ReportEmissionsView, EmissionsView, EmissionView
from api.views import PrivateExportView, PrivateXlsxExportView, EmissionsExportView, EmissionsXlsxExportView
from api.views import EmissionFactorsFile

urlpatterns = {
    path("ademeUser/", AdemeUserView.as_view(), name="ademe_user"),
    path("bilans/", ReportsView.as_view(), name="reports"),
    path("bilans/<int:pk>", ReportView.as_view(), name="report"),
    path("bilans/<int:report_pk>/emissions", ReportEmissionsView.as_view(), name="report_emissions"),
    path("emissions/", EmissionsView.as_view(), name="emissions"),
    path("emissions/<int:pk>", EmissionView.as_view(), name="emission"),
    path("export/", PrivateExportView.as_view(), name="private-csv-export"),
    path("xlsxExport/", PrivateXlsxExportView.as_view({"get": "list"}), name="private-xlsx-export"),
    path("emissionsExport/<int:report_pk>", EmissionsExportView.as_view(), name="emissions-csv-export"),
    path(
        "emissionsXlsxExport/<int:report_pk>",
        EmissionsXlsxExportView.as_view({"get": "list"}),
        name="emissions-xlsx-export",
    ),
    path("emissionFactors/", EmissionFactorsFile.as_view(), name="ef-file"),
    path("ademeAccount/", CreateAccountView.as_view(), name="create-account"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
