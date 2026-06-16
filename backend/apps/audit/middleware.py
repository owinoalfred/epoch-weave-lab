from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if request.path.startswith("/api/") and request.method in ("POST", "PUT", "PATCH", "DELETE"):
                AuditLog.objects.create(
                    user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                    method=request.method,
                    path=request.path[:255],
                    status_code=response.status_code,
                    ip=request.META.get("REMOTE_ADDR"),
                )
        except Exception:
            pass
        return response
