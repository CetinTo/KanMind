# 1. Third-party
from rest_framework import permissions


class IsBoardOwner(permissions.BasePermission):
    """
    Only allows the board owner to make changes.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsBoardMemberOrOwner(permissions.BasePermission):
    """
    Allows access for board owners and members.
    """

    def has_object_permission(self, request, view, obj):
        # For Board objects
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user in obj.members.all()

        # For Column objects
        if hasattr(obj, 'board'):
            board = obj.board
            return board.owner == request.user or request.user in board.members.all()

        # For Task objects
        if hasattr(obj, 'column'):
            board = obj.column.board
            return board.owner == request.user or request.user in board.members.all()

        return False


class IsCommentAuthor(permissions.BasePermission):
    """
    Only allows the comment author to edit/delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
