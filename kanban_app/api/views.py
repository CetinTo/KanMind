# 1. Drittanbieter
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# 2. Lokale Importe
from kanban_app.models import Board, Column, Comment, Subtask, Task
from .permissions import IsBoardMemberOrOwner, IsCommentAuthor
from .serializers import (
    BoardListSerializer,
    BoardSerializer,
    ColumnSerializer,
    CommentSerializer,
    SubtaskSerializer,
    TaskListSerializer,
    TaskSerializer,
)


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Board CRUD-Operationen.

    list:   GET    /api/boards/
    create: POST   /api/boards/
    read:   GET    /api/boards/{id}/
    update: PUT    /api/boards/{id}/
    delete: DELETE /api/boards/{id}/
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]

    def get_queryset(self):
        """Gibt nur Boards zurück, bei denen der User Eigentümer oder Mitglied ist."""
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().prefetch_related('columns', 'members')

    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        return BoardSerializer

    def perform_create(self, serializer):
        """Erstellt ein neues Board mit Standard-Spalten."""
        board = serializer.save(owner=self.request.user)

        # Erstelle Standard-Spalten (4 für Frontend-Kompatibilität)
        Column.objects.bulk_create([
            Column(board=board, title='To Do', position=0),
            Column(board=board, title='In Progress', position=1),
            Column(board=board, title='Review', position=2),
            Column(board=board, title='Done', position=3),
        ])


class ColumnViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Column CRUD-Operationen.

    list:   GET    /api/boards/{board_id}/columns/
    create: POST   /api/boards/{board_id}/columns/
    read:   GET    /api/boards/{board_id}/columns/{id}/
    update: PUT    /api/boards/{board_id}/columns/{id}/
    delete: DELETE /api/boards/{board_id}/columns/{id}/
    """
    serializer_class = ColumnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Gibt Spalten des angegebenen Boards zurück."""
        board_id = self.kwargs.get('board_pk')
        user = self.request.user

        return Column.objects.filter(
            board_id=board_id
        ).filter(
            Q(board__owner=user) | Q(board__members=user)
        ).prefetch_related('tasks')

    def perform_create(self, serializer):
        """Erstellt eine neue Spalte im angegebenen Board."""
        board_id = self.kwargs.get('board_pk')
        board = Board.objects.get(pk=board_id)

        # Setze Position ans Ende
        last_position = Column.objects.filter(board=board).count()
        serializer.save(board=board, position=last_position)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Task CRUD-Operationen.

    list:   GET    /api/tasks/
    create: POST   /api/tasks/
    read:   GET    /api/tasks/{id}/
    update: PUT    /api/tasks/{id}/
    delete: DELETE /api/tasks/{id}/
    move:   PATCH  /api/tasks/{id}/move/
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Gibt Tasks zurück, die zu Boards des Users gehören."""
        user = self.request.user

        return Task.objects.filter(
            Q(column__board__owner=user) | Q(column__board__members=user)
        ).distinct().prefetch_related('subtasks', 'comments', 'assigned_to')

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """
        Gibt alle Tasks zurück, die dem aktuellen User zugewiesen sind.
        GET /api/tasks/assigned-to-me/
        """
        tasks = Task.objects.filter(
            assigned_to=request.user
        ).prefetch_related('subtasks', 'comments', 'assigned_to')

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """
        Gibt alle Tasks zurück, die der User erstellt hat (zum Reviewen).
        GET /api/tasks/reviewing/
        """
        tasks = Task.objects.filter(
            column__board__owner=request.user
        ).exclude(
            assigned_to=request.user
        ).prefetch_related('subtasks', 'comments', 'assigned_to')

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        """
        Verschiebt eine Task in eine andere Spalte oder Position.
        PATCH /api/tasks/{id}/move/
        Body: { "column_id": 2, "position": 0 }
        """
        task = self.get_object()

        column_id = request.data.get('column_id')
        position = request.data.get('position')

        if column_id is not None:
            task.column_id = column_id

        if position is not None:
            task.position = position

        task.save()

        return Response(TaskSerializer(task).data)


class SubtaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Subtask CRUD-Operationen.

    list:   GET    /api/tasks/{task_id}/subtasks/
    create: POST   /api/tasks/{task_id}/subtasks/
    read:   GET    /api/tasks/{task_id}/subtasks/{id}/
    update: PUT    /api/tasks/{task_id}/subtasks/{id}/
    delete: DELETE /api/tasks/{task_id}/subtasks/{id}/
    """
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Gibt Subtasks der angegebenen Task zurück."""
        task_id = self.kwargs.get('task_pk')
        return Subtask.objects.filter(task_id=task_id)

    def perform_create(self, serializer):
        """Erstellt eine neue Subtask."""
        task_id = self.kwargs.get('task_pk')
        serializer.save(task_id=task_id)

    @action(detail=True, methods=['patch'])
    def toggle(self, request, task_pk=None, pk=None):
        """
        Wechselt den Erledigt-Status einer Subtask.
        PATCH /api/tasks/{task_id}/subtasks/{id}/toggle/
        """
        subtask = self.get_object()
        subtask.is_completed = not subtask.is_completed
        subtask.save()

        return Response(SubtaskSerializer(subtask).data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet für Comment CRUD-Operationen.

    list:   GET    /api/tasks/{task_id}/comments/
    create: POST   /api/tasks/{task_id}/comments/
    read:   GET    /api/tasks/{task_id}/comments/{id}/
    update: PUT    /api/tasks/{task_id}/comments/{id}/
    delete: DELETE /api/tasks/{task_id}/comments/{id}/
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def get_queryset(self):
        """Gibt Kommentare der angegebenen Task zurück."""
        task_id = self.kwargs.get('task_pk')
        return Comment.objects.filter(task_id=task_id).select_related('author')

    def perform_create(self, serializer):
        """Erstellt einen neuen Kommentar."""
        task_id = self.kwargs.get('task_pk')
        serializer.save(task_id=task_id, author=self.request.user)
