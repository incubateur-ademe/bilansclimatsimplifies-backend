from rest_framework import permissions
from rest_framework.exceptions import NotFound
from data.models import Emission


class CanManageEmissions(permissions.BasePermission):
    """
    Only the manager of the linked report can manage the report's emissions
    """

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Emission):
            return False
        if request.user != obj.bilan.gestionnaire:
            raise NotFound()
        else:
            return True
