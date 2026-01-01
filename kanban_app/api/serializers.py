# 1. Third-party
from django.contrib.auth.models import User
from rest_framework import serializers

# 2. Local imports
from kanban_app.models import Board, Column, Comment, Subtask, Task


class MemberSerializer(serializers.ModelSerializer):
    """Member serializer with fullname for frontend compatibility."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'fullname']

    def get_fullname(self, obj):
        fullname = f"{obj.first_name} {obj.last_name}".strip()
        return fullname if fullname else obj.username


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representation."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'fullname']

    def get_fullname(self, obj):
        fullname = f"{obj.first_name} {obj.last_name}".strip()
        return fullname if fullname else obj.username


class SubtaskSerializer(serializers.ModelSerializer):
    """Serializer for subtasks."""

    class Meta:
        model = Subtask
        fields = ['id', 'title', 'is_completed']

    def validate_title(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Title must be at least 2 characters long.')
        return value.strip()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    author = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class BoardTaskSerializer(serializers.ModelSerializer):
    """Task serializer for board view (frontend compatible)."""
    status = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'assignee',
            'reviewer',
        ]

    def get_status(self, obj):
        """Converts column title to status slug."""
        title = obj.column.title.lower()
        status_map = {
            'to do': 'to-do',
            'in progress': 'in-progress',
            'review': 'review',
            'done': 'done',
        }
        return status_map.get(title, title.replace(' ', '-'))

    def get_assignee(self, obj):
        """Returns the first assigned user as assignee."""
        assignee = obj.assigned_to.first()
        if assignee:
            return MemberSerializer(assignee).data
        return None

    def get_reviewer(self, obj):
        """Returns the board owner as reviewer (or second assigned user)."""
        if obj.assigned_to.count() > 1:
            reviewer = obj.assigned_to.all()[1]
            return MemberSerializer(reviewer).data
        return None


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task CRUD operations."""
    subtasks = SubtaskSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    status = serializers.CharField(write_only=True, required=False)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    board = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'column',
            'board',
            'status',
            'priority',
            'due_date',
            'position',
            'assignee_id',
            'reviewer_id',
            'subtasks',
            'comments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'column': {'required': False}
        }

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'Title must be at least 3 characters long.')
        return value.strip()

    def create(self, validated_data):
        """Creates task with status-to-column conversion."""
        status = validated_data.pop('status', None)
        board_id = validated_data.pop('board', None)
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        # Ensure column is set
        if 'column' not in validated_data:
            if status and board_id:
                # Convert status to column
                status_map = {
                    'to-do': 'To Do',
                    'in-progress': 'In Progress',
                    'review': 'Review',
                    'done': 'Done',
                }
                column_title = status_map.get(status, 'To Do')
                try:
                    column = Column.objects.get(board_id=board_id, title=column_title)
                    validated_data['column'] = column
                except Column.DoesNotExist:
                    # Fallback: first column of the board
                    column = Column.objects.filter(board_id=board_id).first()
                    if column:
                        validated_data['column'] = column
            elif board_id:
                # If no status but board_id, use first column
                column = Column.objects.filter(board_id=board_id).first()
                if column:
                    validated_data['column'] = column
        
        # Validate that column is set
        if 'column' not in validated_data:
            raise serializers.ValidationError(
                {'column': 'Column is required. Provide either column, or board + status.'}
            )

        task = super().create(validated_data)

        # Assign assignee and reviewer
        if assignee_id:
            task.assigned_to.add(assignee_id)
        if reviewer_id:
            task.assigned_to.add(reviewer_id)

        return task

    def update(self, instance, validated_data):
        """Updates task with status-to-column conversion."""
        status = validated_data.pop('status', None)
        board_id = validated_data.pop('board', None)
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        # Convert status to column
        if status:
            board = instance.column.board
            status_map = {
                'to-do': 'To Do',
                'in-progress': 'In Progress',
                'review': 'Review',
                'done': 'Done',
            }
            column_title = status_map.get(status, status)
            try:
                column = Column.objects.get(board=board, title=column_title)
                validated_data['column'] = column
            except Column.DoesNotExist:
                pass

        task = super().update(instance, validated_data)

        # Update assignee and reviewer
        if assignee_id is not None or reviewer_id is not None:
            task.assigned_to.clear()
            if assignee_id:
                task.assigned_to.add(assignee_id)
            if reviewer_id:
                task.assigned_to.add(reviewer_id)

        return task


class TaskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for task lists."""
    status = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'assignee',
            'reviewer',
        ]

    def get_status(self, obj):
        title = obj.column.title.lower()
        status_map = {
            'to do': 'to-do',
            'in progress': 'in-progress',
            'review': 'review',
            'done': 'done',
        }
        return status_map.get(title, title.replace(' ', '-'))

    def get_assignee(self, obj):
        assignee = obj.assigned_to.first()
        if assignee:
            return MemberSerializer(assignee).data
        return None

    def get_reviewer(self, obj):
        if obj.assigned_to.count() > 1:
            reviewer = obj.assigned_to.all()[1]
            return MemberSerializer(reviewer).data
        return None


class ColumnSerializer(serializers.ModelSerializer):
    """Serializer for columns."""
    tasks = TaskListSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Column
        fields = ['id', 'title', 'position', 'tasks', 'task_count']
        read_only_fields = ['id']

    def get_task_count(self, obj):
        return obj.tasks.count()

    def validate_title(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Title must be at least 2 characters long.')
        return value.strip()


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for boards (detail view) - frontend compatible."""
    owner = MemberSerializer(read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        source='members',
        required=False
    )

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'description',
            'owner',
            'members',
            'member_ids',
            'tasks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_tasks(self, obj):
        """Returns all tasks of the board."""
        tasks = Task.objects.filter(column__board=obj).prefetch_related('assigned_to')
        return BoardTaskSerializer(tasks, many=True).data

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'Title must be at least 3 characters long.')
        return value.strip()


class BoardListSerializer(serializers.ModelSerializer):
    """Simplified serializer for board lists."""
    owner = MemberSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'description',
            'owner',
            'member_count',
            'task_count',
            'updated_at',
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_task_count(self, obj):
        return Task.objects.filter(column__board=obj).count()
