# 1. Drittanbieter
from django.contrib.auth.models import User
from rest_framework import serializers

# 2. Lokale Importe
from auth_app.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer für das Benutzerprofil."""

    class Meta:
        model = UserProfile
        fields = ['id', 'avatar_color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer für Benutzerinformationen."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'profile']
        read_only_fields = ['id']


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer für die Benutzerregistrierung."""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password',
                  'password_confirm', 'first_name', 'last_name']

    def validate_email(self, value):
        """Prüft, ob die E-Mail bereits existiert."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Diese E-Mail-Adresse wird bereits verwendet.')
        return value

    def validate(self, attrs):
        """Prüft, ob die Passwörter übereinstimmen."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Die Passwörter stimmen nicht überein.'
            })
        return attrs

    def create(self, validated_data):
        """Erstellt einen neuen Benutzer mit Profil."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Erstelle automatisch ein Profil
        UserProfile.objects.create(user=user)

        return user
