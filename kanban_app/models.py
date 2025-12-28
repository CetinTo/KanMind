# 1. Drittanbieter
from django.contrib.auth.models import User
from django.db import models


class Board(models.Model):
    """
    Kanban Board - Hauptcontainer für Spalten und Aufgaben.
    """
    title = models.CharField(max_length=200, verbose_name='Titel')
    description = models.TextField(blank=True, verbose_name='Beschreibung')
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_boards',
        verbose_name='Eigentümer'
    )
    members = models.ManyToManyField(
        User,
        related_name='member_boards',
        blank=True,
        verbose_name='Mitglieder'
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
    Spalte eines Boards (z.B. To Do, In Progress, Done).
    """
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name='Board'
    )
    title = models.CharField(max_length=100, verbose_name='Titel')
    position = models.PositiveIntegerField(default=0, verbose_name='Position')

    class Meta:
        verbose_name = 'Spalte'
        verbose_name_plural = 'Spalten'
        ordering = ['position']

    def __str__(self):
        return f"{self.board.title} - {self.title}"


class Task(models.Model):
    """
    Aufgabe/Ticket innerhalb einer Spalte.
    """
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Niedrig'),
        (PRIORITY_MEDIUM, 'Mittel'),
        (PRIORITY_HIGH, 'Hoch'),
    ]

    title = models.CharField(max_length=200, verbose_name='Titel')
    description = models.TextField(blank=True, verbose_name='Beschreibung')
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Spalte'
    )
    assigned_to = models.ManyToManyField(
        User,
        related_name='assigned_tasks',
        blank=True,
        verbose_name='Zugewiesen an'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        verbose_name='Priorität'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fälligkeitsdatum'
    )
    position = models.PositiveIntegerField(default=0, verbose_name='Position')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aufgabe'
        verbose_name_plural = 'Aufgaben'
        ordering = ['position']

    def __str__(self):
        return self.title


class Subtask(models.Model):
    """
    Unteraufgabe einer Aufgabe.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks',
        verbose_name='Aufgabe'
    )
    title = models.CharField(max_length=200, verbose_name='Titel')
    is_completed = models.BooleanField(default=False, verbose_name='Erledigt')

    class Meta:
        verbose_name = 'Unteraufgabe'
        verbose_name_plural = 'Unteraufgaben'
        ordering = ['id']

    def __str__(self):
        status = '✓' if self.is_completed else '○'
        return f"{status} {self.title}"


class Comment(models.Model):
    """
    Kommentar zu einer Aufgabe.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Aufgabe'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Autor'
    )
    content = models.TextField(verbose_name='Inhalt')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kommentar'
        verbose_name_plural = 'Kommentare'
        ordering = ['-created_at']

    def __str__(self):
        return f"Kommentar von {self.author.username} zu {self.task.title}"
