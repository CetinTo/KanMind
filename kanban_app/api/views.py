# 1. Third-party
from django.db.models import Q
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# 2. Local imports
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
    ViewSet for Board CRUD operations.

    list:   GET    /api/boards/
    create: POST   /api/boards/
    read:   GET    /api/boards/{id}/
    update: PUT    /api/boards/{id}/
    delete: DELETE /api/boards/{id}/
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]

    def get_queryset(self):
        """Returns only boards where the user is owner or member."""
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().prefetch_related('columns', 'members')

    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        return BoardSerializer

    def perform_create(self, serializer):
        """Creates a new board with default columns."""
        board = serializer.save(owner=self.request.user)

        # Create default columns (4 for frontend compatibility)
        Column.objects.bulk_create([
            Column(board=board, title='To Do', position=0),
            Column(board=board, title='In Progress', position=1),
            Column(board=board, title='Review', position=2),
            Column(board=board, title='Done', position=3),
        ])


class ColumnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Column CRUD operations.

    list:   GET    /api/boards/{board_id}/columns/
    create: POST   /api/boards/{board_id}/columns/
    read:   GET    /api/boards/{board_id}/columns/{id}/
    update: PUT    /api/boards/{board_id}/columns/{id}/
    delete: DELETE /api/boards/{board_id}/columns/{id}/
    """
    serializer_class = ColumnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Returns columns of the specified board."""
        board_id = self.kwargs.get('board_pk')
        user = self.request.user

        if board_id:
            return Column.objects.filter(
                board_id=board_id
            ).filter(
                Q(board__owner=user) | Q(board__members=user)
            ).distinct().prefetch_related('tasks')
        
        return Column.objects.none()

    def perform_create(self, serializer):
        """Creates a new column in the specified board."""
        board_id = self.kwargs.get('board_pk')
        board = Board.objects.get(pk=board_id)

        # Set position to end
        last_position = Column.objects.filter(board=board).count()
        serializer.save(board=board, position=last_position)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations.

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
        """Returns tasks belonging to the user's boards."""
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
        Returns all tasks assigned to the current user.
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
        Returns all tasks the user created (for reviewing).
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
        Moves a task to another column or position.
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
    ViewSet for Subtask CRUD operations.

    list:   GET    /api/tasks/{task_id}/subtasks/
    create: POST   /api/tasks/{task_id}/subtasks/
    read:   GET    /api/tasks/{task_id}/subtasks/{id}/
    update: PUT    /api/tasks/{task_id}/subtasks/{id}/
    delete: DELETE /api/tasks/{task_id}/subtasks/{id}/
    """
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Returns subtasks of the specified task."""
        task_id = self.kwargs.get('task_pk')
        if not task_id:
            return Subtask.objects.none()
        return Subtask.objects.filter(task_id=task_id)

    def perform_create(self, serializer):
        """Creates a new subtask."""
        task_id = self.kwargs.get('task_pk')
        if not task_id:
            raise serializers.ValidationError({'task': 'Task ID is required.'})
        
        # Verify task exists
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise serializers.ValidationError({'task': 'Task not found.'})
        
        serializer.save(task=task)

    @action(detail=True, methods=['patch'])
    def toggle(self, request, task_pk=None, pk=None):
        """
        Toggles the completed status of a subtask.
        PATCH /api/tasks/{task_id}/subtasks/{id}/toggle/
        """
        subtask = self.get_object()
        subtask.is_completed = not subtask.is_completed
        subtask.save()

        return Response(SubtaskSerializer(subtask).data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Comment CRUD operations.

    list:   GET    /api/tasks/{task_id}/comments/
    create: POST   /api/tasks/{task_id}/comments/
    read:   GET    /api/tasks/{task_id}/comments/{id}/
    update: PUT    /api/tasks/{task_id}/comments/{id}/
    delete: DELETE /api/tasks/{task_id}/comments/{id}/
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def get_queryset(self):
        """Returns comments of the specified task."""
        task_id = self.kwargs.get('task_pk')
        if not task_id:
            return Comment.objects.none()
        return Comment.objects.filter(task_id=task_id).select_related('author')

    def perform_create(self, serializer):
        """Creates a new comment."""
        task_id = self.kwargs.get('task_pk')
        if not task_id:
            raise serializers.ValidationError({'task': 'Task ID is required.'})
        
        # Verify task exists
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise serializers.ValidationError({'task': 'Task not found.'})
        
        serializer.save(task=task, author=self.request.user)
