# 1. Drittanbieter
from django.contrib.auth.models import User
from rest_framework import serializers

# 2. Lokale Importe
from kanban_app.models import Board, Column, Comment, Subtask, Task


class MemberSerializer(serializers.ModelSerializer):
    """Member-Serializer mit fullname für Frontend-Kompatibilität."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'fullname']

    def get_fullname(self, obj):
        fullname = f"{obj.first_name} {obj.last_name}".strip()
        return fullname if fullname else obj.username


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimaler User-Serializer für verschachtelte Darstellung."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'fullname']

    def get_fullname(self, obj):
        fullname = f"{obj.first_name} {obj.last_name}".strip()
        return fullname if fullname else obj.username


class SubtaskSerializer(serializers.ModelSerializer):
    """Serializer für Unteraufgaben."""

    class Meta:
        model = Subtask
        fields = ['id', 'title', 'is_completed']

    def validate_title(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Der Titel muss mindestens 2 Zeichen lang sein.')
        return value.strip()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer für Kommentare."""
    author = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class BoardTaskSerializer(serializers.ModelSerializer):
    """Task-Serializer für Board-Ansicht (Frontend-kompatibel)."""
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
        """Konvertiert Column-Titel zu Status-Slug."""
        title = obj.column.title.lower()
        status_map = {
            'to do': 'to-do',
            'in progress': 'in-progress',
            'review': 'review',
            'done': 'done',
        }
        return status_map.get(title, title.replace(' ', '-'))

    def get_assignee(self, obj):
        """Gibt den ersten zugewiesenen User als assignee zurück."""
        assignee = obj.assigned_to.first()
        if assignee:
            return MemberSerializer(assignee).data
        return None

    def get_reviewer(self, obj):
        """Gibt den Board-Owner als Reviewer zurück (oder zweiten assigned User)."""
        if obj.assigned_to.count() > 1:
            reviewer = obj.assigned_to.all()[1]
            return MemberSerializer(reviewer).data
        return None


class TaskSerializer(serializers.ModelSerializer):
    """Serializer für Task CRUD-Operationen."""
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
                'Der Titel muss mindestens 3 Zeichen lang sein.')
        return value.strip()

    def create(self, validated_data):
        """Erstellt Task mit Status-zu-Column Konvertierung."""
        status = validated_data.pop('status', None)
        board_id = validated_data.pop('board', None)
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        # Status zu Column konvertieren
        if status and board_id and 'column' not in validated_data:
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
                # Fallback: erste Column des Boards
                column = Column.objects.filter(board_id=board_id).first()
                if column:
                    validated_data['column'] = column

        task = super().create(validated_data)

        # Assignee und Reviewer zuweisen
        if assignee_id:
            task.assigned_to.add(assignee_id)
        if reviewer_id:
            task.assigned_to.add(reviewer_id)

        return task

    def update(self, instance, validated_data):
        """Aktualisiert Task mit Status-zu-Column Konvertierung."""
        status = validated_data.pop('status', None)
        board_id = validated_data.pop('board', None)
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        # Status zu Column konvertieren
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

        # Assignee und Reviewer aktualisieren
        if assignee_id is not None or reviewer_id is not None:
            task.assigned_to.clear()
            if assignee_id:
                task.assigned_to.add(assignee_id)
            if reviewer_id:
                task.assigned_to.add(reviewer_id)

        return task


class TaskListSerializer(serializers.ModelSerializer):
    """Vereinfachter Serializer für Task-Listen."""
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
    """Serializer für Spalten."""
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
                'Der Titel muss mindestens 2 Zeichen lang sein.')
        return value.strip()


class BoardSerializer(serializers.ModelSerializer):
    """Serializer für Boards (Detail-Ansicht) - Frontend-kompatibel."""
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
        """Gibt alle Tasks des Boards zurück."""
        tasks = Task.objects.filter(column__board=obj).prefetch_related('assigned_to')
        return BoardTaskSerializer(tasks, many=True).data

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'Der Titel muss mindestens 3 Zeichen lang sein.')
        return value.strip()


class BoardListSerializer(serializers.ModelSerializer):
    """Vereinfachter Serializer für Board-Listen."""
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
