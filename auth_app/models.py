# 1. Drittanbieter
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Erweitertes Benutzerprofil für zusätzliche Informationen.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar_color = models.CharField(
        max_length=7,
        default='#4CAF50',
        verbose_name='Avatar-Farbe'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Benutzerprofil'
        verbose_name_plural = 'Benutzerprofile'
        ordering = ['-created_at']

    def __str__(self):
        return f"Profil von {self.user.username}"
