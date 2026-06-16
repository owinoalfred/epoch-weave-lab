from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    DEAN = "DEAN", "Dean"
    HOD = "HOD", "Head of Department"
    TIMETABLE_OFFICER = "TIMETABLE_OFFICER", "Timetable Officer"
    LECTURER = "LECTURER", "Lecturer"
    LAB_ASSISTANT = "LAB_ASSISTANT", "Lab Assistant"
    STUDENT = "STUDENT", "Student"


class User(AbstractUser):
    """Custom user. Roles are stored on a dedicated UserRole table for RBAC."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        indexes = [models.Index(fields=["email"])]

    def has_role(self, role: str) -> bool:
        return self.roles.filter(role=role).exists()

    @property
    def role_list(self):
        return list(self.roles.values_list("role", flat=True))


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=32, choices=Role.choices)
    scope_department = models.ForeignKey(
        "academics.Department", null=True, blank=True, on_delete=models.SET_NULL
    )
    scope_faculty = models.ForeignKey(
        "academics.Faculty", null=True, blank=True, on_delete=models.SET_NULL
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "role", "scope_department", "scope_faculty")]
        indexes = [models.Index(fields=["role"])]
