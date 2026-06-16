from celery import shared_task
from .services import generate_for_semester


@shared_task(bind=True)
def generate_timetable_task(self, semester_id: int, name: str, user_id: int | None = None,
                             time_limit_seconds: int = 30):
    tt = generate_for_semester(
        semester_id=semester_id, name=name,
        time_limit_seconds=time_limit_seconds, user_id=user_id,
    )
    return {
        "timetable_id": tt.id, "status": tt.status,
        "score": tt.optimization_score, "entries": tt.entries.count(),
    }
