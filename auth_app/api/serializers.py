# 1. Third-party
from django.contrib.auth.models import User
from rest_framework import serializers

# 2. Local imports
from auth_app.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    class Meta:
        model = UserProfile
        fields = ['id', 'avatar_color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user information."""
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'first_name', 'last_name', 'profile']
        read_only_fields = ['id']


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
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
        """Checks if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'This email address is already in use.')
        return value

    def validate(self, attrs):
        """Checks if passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        """Creates a new user with profile."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Automatically create a profile
        UserProfile.objects.create(user=user)

        return user
