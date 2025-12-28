"""
URL configuration for KanMind Backend.
"""

# 1. Drittanbieter
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.api.urls')),
    path('api/', include('kanban_app.api.urls')),
]
