from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Simple custom user. No complex roles or RBAC."""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return self.email