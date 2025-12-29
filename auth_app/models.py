# 1. Third-party
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Extended user profile for additional information.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar_color = models.CharField(
        max_length=7,
        default='#4CAF50',
        verbose_name='Avatar color'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"Profile of {self.user.username}"
