from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-at"]
        indexes = [models.Index(fields=["user", "at"]), models.Index(fields=["path"])]


class Notification(models.Model):
    recipient = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
