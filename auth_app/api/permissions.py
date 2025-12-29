# 1. Third-party
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Only allows the owner to edit an object.
    """

    def has_object_permission(self, request, view, obj):
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access only for the owner
        return obj.user == request.user
