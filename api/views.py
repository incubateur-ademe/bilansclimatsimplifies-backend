from django.contrib.auth import get_user_model
from django.core.exceptions import BadRequest
from django.db import transaction
from django.db.utils import IntegrityError
from django.http.response import JsonResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, NotAuthenticated
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
    ListAPIView,
)
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView
from api.serializers import ReportSerializer, PrivateReportExportSerializer
from api.serializers import UserSerializer, EmissionSerializer, EmissionExportSerializer
from data.models import Report, Emission
from .permissions import CanManageReport, CanManageEmissions
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_csv import renderers as r
from .utils import camelize
from data.emission_factors import get_emission_factors
from rest_framework.viewsets import ReadOnlyModelViewSet
from drf_excel.mixins import XLSXFileMixin
from drf_excel.renderers import XLSXRenderer


class AdemeUserView(APIView):
    """
    API endpoint that allows users to be viewed or edited.
    """

    def get(self, _):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated()
        data = UserSerializer(self.request.user).data
        return JsonResponse(camelize(data), status=status.HTTP_200_OK)

    def post(self, request):
        token = None
        try:
            token = self._get_token(request.data["token"])
        except KeyError:
            raise BadRequest("Expected 'token' in payload")
        user_payload = token
        try:
            with transaction.atomic():
                user = get_user_model().objects.get(ademe_id=user_payload["sub"])
                user.username = user_payload["preferred_username"]
                user.email = user_payload["email"]
                user.first_name = user_payload["given_name"]
                user.last_name = user_payload["family_name"]
                user.save()
        except get_user_model().DoesNotExist:
            get_user_model().objects.create_user(
                ademe_id=user_payload["sub"],
                username=user_payload["preferred_username"],
                email=user_payload["email"],
                first_name=user_payload["given_name"],
                last_name=user_payload["family_name"],
            )
        return Response({}, status=HTTP_201_CREATED)

    # wrap to allow for patching in tests
    @staticmethod
    def _get_token(token):
        return UntypedToken(token)


class ReportsView(ListCreateAPIView):
    model = Report
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Report.objects.filter(gestionnaire=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            serializer.save(gestionnaire=self.request.user)
        except IntegrityError:
            raise BadRequest()


class ReportView(RetrieveUpdateDestroyAPIView):
    model = Report
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageReport]
    queryset = Report.objects.all()


class ReportEmissionsView(ListAPIView):
    model = Emission
    serializer_class = EmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        report_id = self.request.parser_context.get("kwargs").get("report_pk")
        report = Report.objects.get(pk=report_id)
        if report.gestionnaire != self.request.user:
            raise NotFound()
        return Emission.objects.filter(bilan=report_id)


class EmissionsView(CreateAPIView):
    model = Emission
    serializer_class = EmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        report = serializer.validated_data["bilan"]
        if report.gestionnaire != self.request.user:
            raise NotFound()
        serializer.save()


class EmissionView(RetrieveUpdateDestroyAPIView):
    model = Emission
    serializer_class = EmissionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmissions]
    queryset = Emission.objects.all()


class PrivateReportExportRenderer(r.CSVRenderer):
    header = [
        "siren",
        "annee",
        "raison_sociale",
        "region",
        "nom_region",
        "naf",
        "nom_naf",
        "nombre_salaries",
        "mode",
        "poste_1_t",
        "poste_2_t",
        "total_t",
        "statut",
        "creation_date",
        "publication_date",
        "gestionnaire_email",
        "gestionnaire_first_name",
        "gestionnaire_last_name",
    ]
    labels = {
        **PrivateReportExportSerializer.get_labels(),
        **{
            "gestionnaire_email": "Email du créateur du bilan",
            "gestionnaire_first_name": "Prénom du créateur du bilan",
            "gestionnaire_last_name": "Nom du créateur du bilan",
        },
    }


class PrivateExportView(ListAPIView):
    renderer_classes = (PrivateReportExportRenderer,)
    model = Report
    serializer_class = PrivateReportExportSerializer
    queryset = Report.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def finalize_response(self, request, response, *args, **kwargs):
        response["Content-Disposition"] = "attachment; filename=%s" % (self.get_filename())
        return super().finalize_response(request, response, *args, **kwargs)

    def get_filename(self):
        timestamp = timezone.now().strftime("%Y-%m-%d")
        return f"bilans_climat_simplifies_{timestamp}.csv"


class PrivateXlsxExportView(XLSXFileMixin, ReadOnlyModelViewSet):
    queryset = Report.objects.all()
    serializer_class = PrivateReportExportSerializer
    renderer_classes = [XLSXRenderer]
    permission_classes = [permissions.IsAdminUser]
    xlsx_use_labels = True
    column_header = {
        "height": 20,
        "style": {
            "font": {
                "bold": True,
            },
        },
    }
    body = {
        "style": {
            "alignment": {
                "horizontal": "left",
                "vertical": "center",
            },
        },
        "height": 20,
    }

    def get_filename(self, request):
        timestamp = timezone.now().strftime("%Y-%m-%d")
        return f"bilans_climat_simplifies_{timestamp}.xlsx"


class EmissionExportRenderer(r.CSVRenderer):
    header = ["type", "valeur", "unite", "facteur_d_emission", "resultat", "poste", "localisation", "note"]
    labels = EmissionExportSerializer.get_labels()


class EmissionsExportView(ListAPIView):
    renderer_classes = (EmissionExportRenderer,)
    model = Emission
    serializer_class = EmissionExportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        report_id = self.request.parser_context.get("kwargs").get("report_pk")
        report = Report.objects.get(pk=report_id)
        if report.gestionnaire != self.request.user:
            raise NotFound()
        return Emission.objects.filter(bilan=report_id)

    def finalize_response(self, request, response, *args, **kwargs):
        if response.status_code == 200:
            response["Content-Disposition"] = "attachment; filename=%s" % (self.get_filename())
        return super().finalize_response(request, response, *args, **kwargs)

    def get_filename(self):
        report_id = self.request.parser_context.get("kwargs").get("report_pk")
        report = Report.objects.get(pk=report_id)
        return f"export_{report.siren}_{report.annee}.csv"


class EmissionsXlsxExportView(XLSXFileMixin, ReadOnlyModelViewSet):
    queryset = Emission.objects.all()
    serializer_class = EmissionExportSerializer
    renderer_classes = [XLSXRenderer]
    permission_classes = [permissions.IsAuthenticated]
    xlsx_use_labels = True
    column_header = {
        "height": 20,
        "style": {
            "font": {
                "bold": True,
            },
        },
    }
    body = {
        "style": {
            "alignment": {
                "horizontal": "left",
                "vertical": "center",
            },
        },
        "height": 20,
    }

    def get_queryset(self):
        report_id = self.request.parser_context.get("kwargs").get("report_pk")
        report = Report.objects.get(pk=report_id)
        if report.gestionnaire != self.request.user:
            raise NotFound()
        return Emission.objects.filter(bilan=report_id)

    def get_filename(self, request, report_pk):
        report = Report.objects.get(pk=report_pk)
        return f"export_{report.siren}_{report.annee}.xlsx"


class EmissionFactorsFile(APIView):
    def get(self, _):
        return JsonResponse(get_emission_factors().emission_factors, status=status.HTTP_200_OK)
