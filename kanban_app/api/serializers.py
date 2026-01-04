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
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'author', 'created_at']

    def get_author(self, obj):
        """Returns the full name of the author."""
        fullname = f"{obj.author.first_name} {obj.author.last_name}".strip()
        if not fullname:
            fullname = obj.author.username
        return fullname


class BoardTaskSerializer(serializers.ModelSerializer):
    """Task serializer for board view (frontend compatible)."""
    status = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

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
            'comments_count',
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
        assigned_users = list(obj.assigned_to.all())
        reviewer_id = getattr(obj, '_reviewer_id', None)
        has_assignee = getattr(obj, '_has_assignee', None)
        
        # If reviewer_id was set but no assignee, assignee is null
        if reviewer_id is not None and has_assignee is False:
            return None
        
        # If reviewer_id was set, make sure first user is not the reviewer
        if reviewer_id is not None and len(assigned_users) == 1:
            if assigned_users[0].id == reviewer_id:
                return None
        
        if assigned_users:
            return MemberSerializer(assigned_users[0]).data
        return None

    def get_reviewer(self, obj):
        """Returns the reviewer (second assigned user, or first if only reviewer exists)."""
        assigned_users = list(obj.assigned_to.all())
        reviewer_id = getattr(obj, '_reviewer_id', None)
        has_assignee = getattr(obj, '_has_assignee', None)
        
        # If reviewer_id was explicitly set, always return reviewer as object
        if reviewer_id is not None:
            # Find reviewer by ID in assigned_users
            for user in assigned_users:
                if user.id == reviewer_id:
                    return MemberSerializer(user).data
            # If reviewer_id was set but not found, try to get it from database
            from django.contrib.auth.models import User
            try:
                reviewer_user = User.objects.get(id=reviewer_id)
                return MemberSerializer(reviewer_user).data
            except User.DoesNotExist:
                pass
        
        # Fallback: if 2+ users, reviewer is the second one
        if len(assigned_users) > 1:
            reviewer = assigned_users[1]
            return MemberSerializer(reviewer).data
        # If only one user and no assignee, it's the reviewer
        elif len(assigned_users) == 1 and has_assignee is False:
            return MemberSerializer(assigned_users[0]).data
        
        return None

    def get_comments_count(self, obj):
        """Returns the number of comments for the task."""
        return obj.comments.count()


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
                    else:
                        raise serializers.ValidationError(
                            {'board': f'Board {board_id} has no columns. Please create columns first.'}
                        )
            elif board_id:
                # If no status but board_id, use first column
                column = Column.objects.filter(board_id=board_id).first()
                if column:
                    validated_data['column'] = column
                else:
                    raise serializers.ValidationError(
                        {'board': f'Board {board_id} has no columns. Please create columns first.'}
                    )
        
        # Validate that column is set
        if 'column' not in validated_data:
            raise serializers.ValidationError(
                {'column': 'Column is required. Provide either column, or board + status.'}
            )

        # Set created_by to current user before creating
        validated_data['created_by'] = self.context['request'].user
        task = super().create(validated_data)

        # Assign assignee and reviewer (validate user existence)
        # Important: assignee must be first, reviewer must be second
        # Store reviewer_id in task for later reference
        from django.contrib.auth.models import User
        if assignee_id:
            try:
                assignee_user = User.objects.get(id=assignee_id)
                task.assigned_to.add(assignee_user)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'assignee_id': f'User with ID {assignee_id} does not exist.'}
                )
        if reviewer_id:
            try:
                reviewer_user = User.objects.get(id=reviewer_id)
                task.assigned_to.add(reviewer_user)
                # Store reviewer_id for later reference
                task._reviewer_id = reviewer_id
                task._has_assignee = bool(assignee_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {'reviewer_id': f'User with ID {reviewer_id} does not exist.'}
                )

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
        # Important: assignee must be first, reviewer must be second
        if assignee_id is not None or reviewer_id is not None:
            task.assigned_to.clear()
            if assignee_id:
                task.assigned_to.add(assignee_id)
            if reviewer_id:
                task.assigned_to.add(reviewer_id)
                # Store reviewer_id for later reference
                task._reviewer_id = reviewer_id
                task._has_assignee = bool(assignee_id)

        return task


class TaskListSerializer(serializers.ModelSerializer):
    """Simplified serializer for task lists."""
    status = serializers.SerializerMethodField()
    assignee = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()
    board = serializers.IntegerField(source='column.board.id', read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'board',
            'title',
            'description',
            'status',
            'priority',
            'assignee',
            'reviewer',
            'due_date',
            'comments_count',
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
        """Returns the first assigned user as assignee."""
        assigned_users = list(obj.assigned_to.all())
        reviewer_id = getattr(obj, '_reviewer_id', None)
        has_assignee = getattr(obj, '_has_assignee', None)
        
        # If reviewer_id was set but no assignee, assignee is null
        if reviewer_id is not None and has_assignee is False:
            return None
        
        # If reviewer_id was set, make sure first user is not the reviewer
        if reviewer_id is not None and len(assigned_users) == 1:
            if assigned_users[0].id == reviewer_id:
                return None
        
        if assigned_users:
            return MemberSerializer(assigned_users[0]).data
        return None

    def get_reviewer(self, obj):
        """Returns the reviewer (second assigned user, or first if only reviewer exists)."""
        assigned_users = list(obj.assigned_to.all())
        reviewer_id = getattr(obj, '_reviewer_id', None)
        has_assignee = getattr(obj, '_has_assignee', None)
        
        # If reviewer_id was explicitly set, always return reviewer as object
        if reviewer_id is not None:
            # Find reviewer by ID in assigned_users
            for user in assigned_users:
                if user.id == reviewer_id:
                    return MemberSerializer(user).data
            # If reviewer_id was set but not found, try to get it from database
            from django.contrib.auth.models import User
            try:
                reviewer_user = User.objects.get(id=reviewer_id)
                return MemberSerializer(reviewer_user).data
            except User.DoesNotExist:
                pass
        
        # Fallback: if 2+ users, reviewer is the second one
        if len(assigned_users) > 1:
            reviewer = assigned_users[1]
            return MemberSerializer(reviewer).data
        # If only one user and no assignee, it's the reviewer
        elif len(assigned_users) == 1 and has_assignee is False:
            return MemberSerializer(assigned_users[0]).data
        
        return None

    def get_comments_count(self, obj):
        """Returns the number of comments for the task."""
        return obj.comments.count()


class TaskUpdateResponseSerializer(serializers.ModelSerializer):
    """Serializer for task update response (without board and comments_count)."""
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
            'assignee',
            'reviewer',
            'due_date',
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
        """Returns the first assigned user as assignee."""
        assigned_users = list(obj.assigned_to.all())
        reviewer_id = getattr(obj, '_reviewer_id', None)
        has_assignee = getattr(obj, '_has_assignee', None)
        
        # If reviewer_id was set but no assignee, assignee is null
        if reviewer_id is not None and has_assignee is False:
            return None
        
        # If reviewer_id was set, make sure first user is not the reviewer
        if reviewer_id is not None and len(assigned_users) == 1:
            if assigned_users[0].id == reviewer_id:
                return None
        
        if assigned_users:
            return MemberSerializer(assigned_users[0]).data
        return None

    def get_reviewer(self, obj):
        """Returns the reviewer (second assigned user, or first if only reviewer exists)."""
        assigned_users = list(obj.assigned_to.all())
        reviewer_id = getattr(obj, '_reviewer_id', None)
        has_assignee = getattr(obj, '_has_assignee', None)
        
        # If reviewer_id was explicitly set, always return reviewer as object
        if reviewer_id is not None:
            # Find reviewer by ID in assigned_users
            for user in assigned_users:
                if user.id == reviewer_id:
                    return MemberSerializer(user).data
            # If reviewer_id was set but not found, try to get it from database
            from django.contrib.auth.models import User
            try:
                reviewer_user = User.objects.get(id=reviewer_id)
                return MemberSerializer(reviewer_user).data
            except User.DoesNotExist:
                pass
        
        # Fallback: if 2+ users, reviewer is the second one
        if len(assigned_users) > 1:
            reviewer = assigned_users[1]
            return MemberSerializer(reviewer).data
        # If only one user and no assignee, it's the reviewer
        elif len(assigned_users) == 1 and has_assignee is False:
            return MemberSerializer(assigned_users[0]).data
        
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


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for board updates (PATCH)."""
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    owner_data = MemberSerializer(source='owner', read_only=True)
    members_data = MemberSerializer(many=True, read_only=True, source='members')

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'owner_data',
            'members',
            'members_data',
        ]
        read_only_fields = ['id', 'owner_data', 'members_data']


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for boards (detail view) - frontend compatible."""
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    members_read = MemberSerializer(many=True, read_only=True, source='members')
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'owner_id',
            'members',
            'members_read',
            'tasks',
        ]
        read_only_fields = ['id', 'owner_id']

    def get_tasks(self, obj):
        """Returns all tasks of the board."""
        tasks = Task.objects.filter(column__board=obj).prefetch_related(
            'assigned_to', 'comments'
        )
        return BoardTaskSerializer(tasks, many=True).data
    
    def to_representation(self, instance):
        """Custom representation to use 'members' instead of 'members_read'."""
        representation = super().to_representation(instance)
        # Replace 'members_read' with 'members' for API response
        if 'members_read' in representation:
            representation['members'] = representation.pop('members_read')
        return representation

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'Title must be at least 3 characters long.')
        return value.strip()


class BoardListSerializer(serializers.ModelSerializer):
    """Simplified serializer for board lists."""
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            'id',
            'title',
            'owner_id',
            'member_count',
            'ticket_count',
            'tasks_to_do_count',
            'tasks_high_prio_count',
        ]

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return Task.objects.filter(column__board=obj).count()

    def get_tasks_to_do_count(self, obj):
        to_do_column = Column.objects.filter(board=obj, title='To Do').first()
        if to_do_column:
            return Task.objects.filter(column=to_do_column).count()
        return 0

    def get_tasks_high_prio_count(self, obj):
        return Task.objects.filter(
            column__board=obj,
            priority=Task.PRIORITY_HIGH
        ).count()
