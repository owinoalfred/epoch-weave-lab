from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, UserSerializer, UniTimeTokenSerializer

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = UniTimeTokenSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    """Stateless JWT logout: client discards tokens. Optionally blacklist refresh."""
    def post(self, request, *args, **kwargs):
        return Response({"detail": "logged out"}, status=status.HTTP_200_OK)
