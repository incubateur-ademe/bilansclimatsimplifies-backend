from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from api.views import AuthenticatedUserView
from api.views import ReportsView, ReportView
from api.views import ReportEmissionsView, EmissionsView, EmissionView

urlpatterns = {
    path("user/", AuthenticatedUserView.as_view(), name="authenticated_user"),
    path("bilans/", ReportsView.as_view(), name="reports"),
    path("bilans/<int:pk>", ReportView.as_view(), name="report"),
    path("bilans/<int:report_pk>/emissions", ReportEmissionsView.as_view(), name="report_emissions"),
    path("emissions/", EmissionsView.as_view(), name="emissions"),
    path("emissions/<int:pk>", EmissionView.as_view(), name="emission"),
}

urlpatterns = format_suffix_patterns(urlpatterns)
