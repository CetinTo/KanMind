# 1. Third-party
from django.contrib import admin

# 2. Local imports
from .models import Board, Column, Comment, Subtask, Task


class ColumnInline(admin.TabularInline):
    model = Column
    extra = 0
    ordering = ['position']


class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner',
                    'member_count', 'created_at', 'updated_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['title', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['members']
    inlines = [ColumnInline]

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['title', 'board', 'position', 'task_count']
    list_filter = ['board']
    search_fields = ['title', 'board__title']
    ordering = ['board', 'position']

    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tasks'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'column', 'priority',
                    'due_date', 'position', 'created_at']
    list_filter = ['priority', 'column__board', 'due_date', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['assigned_to']
    inlines = [SubtaskInline, CommentInline]
    ordering = ['column', 'position']


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'is_completed']
    list_filter = ['is_completed', 'task__column__board']
    search_fields = ['title', 'task__title']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'short_content', 'created_at']
    list_filter = ['author', 'created_at']
    search_fields = ['content', 'task__title', 'author__username']
    readonly_fields = ['created_at', 'updated_at']

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
