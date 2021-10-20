from django.contrib.auth import get_user_model
from django.core.exceptions import BadRequest, PermissionDenied
from django.db import IntegrityError, transaction
from rest_framework import permissions
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, CreateAPIView, ListAPIView
from api.serializers import ReportSerializer, UserSerializer, EmissionSerializer
from data.models import Report, Emission


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


class ReportView(ListCreateAPIView):
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


class ReportEmissionsView(ListAPIView):
    model = Emission
    serializer_class = EmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        report_id = self.request.parser_context.get("kwargs").get("report_pk")
        report = Report.objects.get(pk=report_id)
        if report.gestionnaire != self.request.user:
            raise PermissionDenied()
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
                raise PermissionDenied()
            serializer.save()
        except IntegrityError:
            raise BadRequest()
