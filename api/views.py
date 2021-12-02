from django.contrib.auth import get_user_model
from django.core.exceptions import BadRequest
from django.db import IntegrityError, transaction
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    CreateAPIView,
    ListAPIView,
)
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView
from api.serializers import ReportSerializer, UserSerializer, EmissionSerializer
from data.models import Report, Emission
from .permissions import CanManageReport, CanManageEmissions
from rest_framework_simplejwt.tokens import UntypedToken


class AuthenticatedUserView(RetrieveUpdateAPIView):
    """
    API endpoint that allows users to be viewed or edited.
    """

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = get_user_model().objects.all()

    def get_object(self):
        return self.request.user


class AdemeUserView(APIView):
    """
    API endpoint that allows users to be viewed or edited.
    """

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
        try:
            report = serializer.validated_data["bilan"]
            if report.gestionnaire != self.request.user:
                raise NotFound()
            serializer.save()
        except IntegrityError:
            raise BadRequest()


class EmissionView(RetrieveUpdateDestroyAPIView):
    model = Emission
    serializer_class = EmissionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEmissions]
    queryset = Emission.objects.all()
