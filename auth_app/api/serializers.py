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
    fullname = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    repeated_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']

    def validate_email(self, value):
        """Checks if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'This email address is already in use.')
        return value

    def validate(self, attrs):
        """Checks if passwords match."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({
                'repeated_password': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        """Creates a new user with profile."""
        fullname = validated_data.pop('fullname')
        repeated_password = validated_data.pop('repeated_password')
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        
        # Split fullname into first_name and last_name
        name_parts = fullname.strip().split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate username from email
        username = email.split('@')[0]
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        # Automatically create a profile
        UserProfile.objects.create(user=user)

        return user
