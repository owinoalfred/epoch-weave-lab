from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    UniTimeTokenSerializer,
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """Register a new user."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(TokenObtainPairView):
    """Login and get JWT tokens."""
    serializer_class = UniTimeTokenSerializer

class MeView(APIView):
    """Get current user profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# --- ADDED THIS BACK ---
class LogoutView(APIView):
    """Logout endpoint. (Frontend handles clearing the actual tokens)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)