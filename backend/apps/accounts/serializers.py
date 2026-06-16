from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserRole, Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "phone", "is_active", "roles")

    def get_roles(self, obj):
        return obj.role_list


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=Role.choices, write_only=True, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "role")

    def create(self, validated_data):
        role = validated_data.pop("role", Role.STUDENT)
        user = User.objects.create_user(**validated_data, password=validated_data.pop("password"))
        UserRole.objects.create(user=user, role=role)
        return user


class UniTimeTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["roles"] = user.role_list
        token["email"] = user.email
        token["name"] = f"{user.first_name} {user.last_name}".strip() or user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
