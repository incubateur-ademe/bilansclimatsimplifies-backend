from django.contrib.auth import get_user_model
from django.core.exceptions import BadRequest
from django.db import IntegrityError, transaction
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


class ReportExportRenderer(r.CSVRenderer):
    header = [
        "siren",
        "annee",
        "raison_sociale",
        "region",
        "naf",
        "nombre_salaries",
        "mode",
        "poste_1",
        "poste_2",
        "total",
        "statut",
        "creation_date",
        "publication_date",
        "gestionnaire.email",
        "gestionnaire.first_name",
        "gestionnaire.last_name",
    ]
    labels = {
        "poste_1": "poste_1_tCO2e",
        "poste_2": "poste_2_tCO2e",
        "total": "total_tCO2e",
        "gestionnaire.first_name": "gestionnaire.prenom",
        "gestionnaire.last_name": "gestionnaire.nom",
    }


class PrivateExportView(ListAPIView):
    renderer_classes = (ReportExportRenderer,)
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


class EmissionExportRenderer(r.CSVRenderer):
    header = ["type", "valeur", "unite", "facteur_d_emission", "resultat", "poste", "localisation", "note"]
    labels = {
        "resultat": "resultat_kgCO2e",
    }


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


class EmissionFactorsFile(APIView):
    def get(self, _):
        return JsonResponse(get_emission_factors().emission_factors, status=status.HTTP_200_OK)
