# 1. Third-party
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# 2. Local imports
from .permissions import IsOwnerOrReadOnly
from .serializers import RegistrationSerializer, UserProfileSerializer, UserSerializer


class LoginView(APIView):
    """
    API endpoint for login.
    POST /api/auth/login/
    
    Expects: { "email": "...", "password": "..." }
    Or:      { "username": "...", "password": "..." }
    
    Returns: { "token": "...", "user_id": ..., "email": "...", "fullname": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')

        # Login via email or username
        if email and not username:
            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # Authentication
        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Create or retrieve token
        token, _ = Token.objects.get_or_create(user=user)

        # Compose fullname
        fullname = f"{user.first_name} {user.last_name}".strip()
        if not fullname:
            fullname = user.username

        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'fullname': fullname
        })


class RegistrationView(CreateAPIView):
    """
    API endpoint for user registration.
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create token
        token, _ = Token.objects.get_or_create(user=user)

        # Compose fullname
        fullname = f"{user.first_name} {user.last_name}".strip()
        if not fullname:
            fullname = user.username

        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'fullname': fullname
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    """
    API endpoint for current user.
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserProfileView(RetrieveUpdateAPIView):
    """
    API endpoint for user profile.
    GET/PUT/PATCH /api/auth/profile/
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user.profile
