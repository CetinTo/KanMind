# 1. Third-party
from django.contrib.auth.models import User
from django.db import models


class Board(models.Model):
    """
    Kanban Board - Main container for columns and tasks.
    """
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_boards',
        verbose_name='Owner'
    )
    members = models.ManyToManyField(
        User,
        related_name='member_boards',
        blank=True,
        verbose_name='Members'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Column(models.Model):
    """
    Column of a board (e.g. To Do, In Progress, Done).
    """
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name='Board'
    )
    title = models.CharField(max_length=100, verbose_name='Title')
    position = models.PositiveIntegerField(default=0, verbose_name='Position')

    class Meta:
        verbose_name = 'Column'
        verbose_name_plural = 'Columns'
        ordering = ['position']

    def __str__(self):
        return f"{self.board.title} - {self.title}"


class Task(models.Model):
    """
    Task/Ticket within a column.
    """
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(blank=True, verbose_name='Description')
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Column'
    )
    assigned_to = models.ManyToManyField(
        User,
        related_name='assigned_tasks',
        blank=True,
        verbose_name='Assigned to'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name='Priority'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Due date'
    )
    position = models.PositiveIntegerField(default=0, verbose_name='Position')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['position']

    def __str__(self):
        return self.title


class Subtask(models.Model):
    """
    Subtask of a task.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks',
        verbose_name='Task'
    )
    title = models.CharField(max_length=200, verbose_name='Title')
    is_completed = models.BooleanField(default=False, verbose_name='Completed')

    class Meta:
        verbose_name = 'Subtask'
        verbose_name_plural = 'Subtasks'
        ordering = ['id']

    def __str__(self):
        status = '✓' if self.is_completed else '○'
        return f"{status} {self.title}"


class Comment(models.Model):
    """
    Comment on a task.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Task'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Author'
    )
    content = models.TextField(verbose_name='Content')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
