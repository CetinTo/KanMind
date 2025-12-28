# 1. Drittanbieter
from django.urls import path

# 2. Lokale Importe
from .views import CurrentUserView, LoginView, RegistrationView, UserProfileView

urlpatterns = [
    # Auth Endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
