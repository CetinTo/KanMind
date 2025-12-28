# 1. Drittanbieter
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Erlaubt nur dem Eigentümer das Bearbeiten eines Objekts.
    """

    def has_object_permission(self, request, view, obj):
        # Lesezugriff für alle authentifizierten Benutzer
        if request.method in permissions.SAFE_METHODS:
            return True

        # Schreibzugriff nur für den Eigentümer
        return obj.user == request.user
