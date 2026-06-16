from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from celery.result import AsyncResult
from .tasks import generate_timetable_task
from .services import generate_for_semester


class GenerateRequestSerializer(serializers.Serializer):
    semester_id = serializers.IntegerField()
    name = serializers.CharField(max_length=160)
    time_limit_seconds = serializers.IntegerField(required=False, default=30, min_value=5, max_value=600)
    sync = serializers.BooleanField(required=False, default=False)


class GenerateTimetableView(APIView):
    def post(self, request):
        s = GenerateRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if d["sync"]:
            tt = generate_for_semester(
                semester_id=d["semester_id"], name=d["name"],
                time_limit_seconds=d["time_limit_seconds"],
                user_id=request.user.id if request.user.is_authenticated else None,
            )
            return Response({"timetable_id": tt.id, "status": tt.status,
                             "score": tt.optimization_score,
                             "entries": tt.entries.count()})
        task = generate_timetable_task.delay(
            semester_id=d["semester_id"], name=d["name"],
            user_id=request.user.id if request.user.is_authenticated else None,
            time_limit_seconds=d["time_limit_seconds"],
        )
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class JobStatusView(APIView):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        return Response({
            "task_id": task_id,
            "state": result.state,
            "result": result.result if result.successful() else None,
        })
