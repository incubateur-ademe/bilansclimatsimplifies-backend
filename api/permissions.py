from rest_framework import permissions
from rest_framework.exceptions import NotFound
from data.models import Report, Emission


class CanManageReport(permissions.BasePermission):
    """
    Only manager of report can view and modify it
    """

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Report):
            return False
        if request.user != obj.gestionnaire:
            raise NotFound()
        return super().has_object_permission(request, view, obj)


class CanManageEmissions(permissions.BasePermission):
    """
    Only the manager of the linked report can create, read, update, delete
    emissions for report
    """

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Emission):
            return False
        if request.user != obj.bilan.gestionnaire:
            raise NotFound()
        else:
            return super().has_object_permission(request, view, obj)
