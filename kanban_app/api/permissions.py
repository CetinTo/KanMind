# 1. Drittanbieter
from rest_framework import permissions


class IsBoardOwner(permissions.BasePermission):
    """
    Erlaubt nur dem Board-Eigentümer Änderungen.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsBoardMemberOrOwner(permissions.BasePermission):
    """
    Erlaubt Zugriff für Board-Eigentümer und Mitglieder.
    """

    def has_object_permission(self, request, view, obj):
        # Für Board-Objekte
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user in obj.members.all()

        # Für Column-Objekte
        if hasattr(obj, 'board'):
            board = obj.board
            return board.owner == request.user or request.user in board.members.all()

        # Für Task-Objekte
        if hasattr(obj, 'column'):
            board = obj.column.board
            return board.owner == request.user or request.user in board.members.all()

        return False


class IsCommentAuthor(permissions.BasePermission):
    """
    Erlaubt nur dem Autor eines Kommentars das Bearbeiten/Löschen.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
