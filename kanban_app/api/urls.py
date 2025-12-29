# 1. Third-party
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

# 2. Local imports
from .views import BoardViewSet, ColumnViewSet, CommentViewSet, SubtaskViewSet, TaskViewSet

# Main router
router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'tasks', TaskViewSet, basename='task')

# Nested router: boards/{board_pk}/columns/
boards_router = routers.NestedDefaultRouter(router, r'boards', lookup='board')
boards_router.register(r'columns', ColumnViewSet, basename='board-columns')

# Nested router: tasks/{task_pk}/subtasks/ and tasks/{task_pk}/comments/
tasks_router = routers.NestedDefaultRouter(router, r'tasks', lookup='task')
tasks_router.register(r'subtasks', SubtaskViewSet, basename='task-subtasks')
tasks_router.register(r'comments', CommentViewSet, basename='task-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(boards_router.urls)),
    path('', include(tasks_router.urls)),
]
