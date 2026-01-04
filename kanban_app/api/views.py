# 1. Third-party
from django.db.models import Q
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# 2. Local imports
from kanban_app.models import Board, Column, Comment, Subtask, Task
from .permissions import IsBoardMemberOrOwner, IsCommentAuthor
from .serializers import (
    BoardListSerializer,
    BoardSerializer,
    BoardUpdateSerializer,
    ColumnSerializer,
    CommentSerializer,
    SubtaskSerializer,
    TaskListSerializer,
    TaskSerializer,
    TaskUpdateResponseSerializer,
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
    
    def get_object(self):
        """Override to return 403 instead of 404 for unauthorized access."""
        try:
            obj = super().get_object()
        except Exception:
            # If object not in queryset, check if it exists but user has no permission
            pk = self.kwargs.get('pk')
            if pk:
                try:
                    board = Board.objects.get(pk=pk)
                    user = self.request.user
                    # Check permission first (403)
                    if board.owner != user and user not in board.members.all():
                        from rest_framework.exceptions import PermissionDenied
                        raise PermissionDenied('You do not have permission to access this board.')
                except Board.DoesNotExist:
                    pass
            # Re-raise original exception (404)
            raise
        return obj

    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        elif self.action in ['update', 'partial_update']:
            return BoardUpdateSerializer
        return BoardSerializer

    def create(self, request, *args, **kwargs):
        """Creates a new board with default columns and returns BoardListSerializer format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save(owner=self.request.user)

        # Create default columns (4 for frontend compatibility)
        Column.objects.bulk_create([
            Column(board=board, title='To Do', position=0),
            Column(board=board, title='In Progress', position=1),
            Column(board=board, title='Review', position=2),
            Column(board=board, title='Done', position=3),
        ])

        # Return BoardListSerializer format
        list_serializer = BoardListSerializer(board)
        return Response(list_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Deletes a board. Only the board owner can delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


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
        user = self.request.user
        
        try:
            board = Board.objects.get(pk=board_id)
            # Check permission first (403)
            if board.owner != user and user not in board.members.all():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You must be a member of the board to create columns.')
        except Board.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Board not found.')

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
    
    def get_object(self):
        """Override to return 403 instead of 404 for unauthorized access."""
        try:
            obj = super().get_object()
        except Exception:
            # If object not in queryset, check if it exists but user has no permission
            pk = self.kwargs.get('pk')
            if pk:
                try:
                    task = Task.objects.select_related('column__board').get(pk=pk)
                    board = task.column.board
                    user = self.request.user
                    if board.owner != user and user not in board.members.all():
                        from rest_framework.exceptions import PermissionDenied
                        raise PermissionDenied('You do not have permission to access this task.')
                except Task.DoesNotExist:
                    pass
            # Re-raise original exception (404)
            raise
        return obj

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        if self.action == 'create':
            return TaskSerializer
        if self.action in ['update', 'partial_update']:
            return TaskSerializer
        return TaskSerializer

    def update(self, request, *args, **kwargs):
        """Updates a task and returns it in the list format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check board membership
        board = instance.column.board
        user = request.user
        if board.owner != user and user not in board.members.all():
            return Response(
                {'error': 'You must be a member of the board to update tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        # Reload task with related data for response
        task = Task.objects.select_related('column__board').prefetch_related(
            'subtasks', 'comments', 'assigned_to'
        ).get(id=task.id)
        
        # Preserve reviewer_only flag if it exists
        if hasattr(serializer.instance, '_reviewer_only'):
            task._reviewer_only = serializer.instance._reviewer_only
        
        # Return response using TaskUpdateResponseSerializer format
        response_serializer = TaskUpdateResponseSerializer(task)
        return Response(response_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) for a task."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Deletes a task. Only board owner or task creator can delete."""
        instance = self.get_object()
        
        # Check if user is board owner or task creator
        board = instance.column.board
        user = request.user
        
        if board.owner != user and (not instance.created_by or instance.created_by != user):
            return Response(
                {'error': 'Only the board owner or task creator can delete tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        """Creates a new task and returns it in the list format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate board access
        board_id = request.data.get('board')
        if board_id:
            # First check if user has permission (403), then check if board exists (404)
            user = request.user
            try:
                board = Board.objects.get(id=board_id)
                # Check permission first
                if board.owner != user and user not in board.members.all():
                    return Response(
                        {'error': 'You must be a member of the board to create tasks.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Board.DoesNotExist:
                # Only return 404 if user would have permission (but board doesn't exist)
                # If user has no permission, we already returned 403 above
                return Response(
                    {'error': 'Board not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        task = serializer.save()
        
        # Reload task with related data for response
        task = Task.objects.select_related('column__board').prefetch_related(
            'subtasks', 'comments', 'assigned_to'
        ).get(id=task.id)
        
        # Preserve reviewer_only flag if it exists
        if hasattr(serializer.instance, '_reviewer_only'):
            task._reviewer_only = serializer.instance._reviewer_only
        
        # Return response using TaskListSerializer format
        response_serializer = TaskListSerializer(task)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['get'], url_path='assigned-to-me')
    def assigned_to_me(self, request):
        """
        Returns all tasks assigned to the current user.
        GET /api/tasks/assigned-to-me/
        """
        tasks = Task.objects.filter(
            assigned_to=request.user
        ).select_related('column__board').prefetch_related(
            'subtasks', 'comments', 'assigned_to'
        )

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """
        Returns all tasks where the current user is the reviewer.
        GET /api/tasks/reviewing/
        """
        # Get all tasks where user is in assigned_to
        all_tasks = Task.objects.filter(
            assigned_to=request.user
        ).select_related('column__board').prefetch_related(
            'subtasks', 'comments', 'assigned_to'
        )
        
        # Filter tasks where user is the reviewer (second in assigned_to)
        reviewing_tasks = []
        for task in all_tasks:
            assigned_users = list(task.assigned_to.all())
            if len(assigned_users) > 1 and assigned_users[1].id == request.user.id:
                reviewing_tasks.append(task)

        serializer = TaskListSerializer(reviewing_tasks, many=True)
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
        
        user = self.request.user
        # Verify task exists and check permission first (403)
        try:
            task = Task.objects.select_related('column__board').get(pk=task_id)
            board = task.column.board
            # Check permission first (403)
            if board.owner != user and user not in board.members.all():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You must be a member of the board to create subtasks.')
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

    def list(self, request, *args, **kwargs):
        """List comments with board membership check."""
        task_id = self.kwargs.get('task_pk')
        if task_id:
            user = request.user
            try:
                task = Task.objects.select_related('column__board').get(id=task_id)
                board = task.column.board
                
                # Check permission first (403)
                if board.owner != user and user not in board.members.all():
                    return Response(
                        {'error': 'You must be a member of the board to view comments.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Task.DoesNotExist:
                # Only return 404 if user would have permission (but task doesn't exist)
                # If user has no permission, we already returned 403 above
                return Response(
                    {'error': 'Task not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Creates a new comment and returns it with proper status code."""
        task_id = self.kwargs.get('task_pk')
        if not task_id:
            return Response(
                {'error': 'Task ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if task exists and user has board access
        user = request.user
        try:
            task = Task.objects.select_related('column__board').get(pk=task_id)
            board = task.column.board
            
            # Check permission first (403)
            if board.owner != user and user not in board.members.all():
                return Response(
                    {'error': 'You must be a member of the board to create comments.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Task.DoesNotExist:
            # Only return 404 if user would have permission (but task doesn't exist)
            # If user has no permission, we already returned 403 above
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        
        # Reload comment with author data
        comment = Comment.objects.select_related('author').get(id=comment.id)
        
        response_serializer = CommentSerializer(comment)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        """Deletes a comment. Only the comment author can delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(None, status=status.HTTP_204_NO_CONTENT)
