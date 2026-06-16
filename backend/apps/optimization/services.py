"""Build solver inputs from DB, run solver, persist result as a Timetable."""
from __future__ import annotations
from django.db import transaction
from apps.academics.models import Semester, ProgrammeLevel
from apps.staff.models import CourseAllocation, LecturerRank
from apps.facilities.models import Room
from apps.scheduling.models import (
    Timetable, TimetableEntry, TimeSlot, TimetableStatus, DayOfWeek,
)
from .engine import TimetableSolver, SessionInput, RoomInput


def _max_days_for_level_semester(level: str, semester_number: int) -> int:
    if level in (ProgrammeLevel.MASTERS, ProgrammeLevel.PHD):
        return 1  # Saturday only
    return 4 if semester_number == 1 else 3


def generate_for_semester(semester_id: int, name: str, time_limit_seconds: int = 30,
                          user_id: int | None = None) -> Timetable:
    semester = Semester.objects.get(pk=semester_id)
    allocations = (
        CourseAllocation.objects.filter(semester=semester)
        .select_related("course", "lecturer", "lecturer__user")
        .prefetch_related("student_groups")
    )

    sessions: list[SessionInput] = []
    sid_to_alloc: dict[int, CourseAllocation] = {}
    max_days_per_group: dict[int, int] = {}

    for alloc in allocations:
        groups = list(alloc.student_groups.all())
        if not groups:
            continue
        total_size = sum(g.size for g in groups) or 1
        # split weekly_hours into 2-hour slot sessions
        n_sessions = max(1, alloc.course.weekly_hours // 2)
        for i in range(n_sessions):
            sid = len(sessions) + 1
            sessions.append(SessionInput(
                id=sid,
                course_code=alloc.course.code,
                lecturer_id=alloc.lecturer_id,
                lecturer_max_hours=LecturerRank.max_hours(alloc.lecturer.rank),
                group_ids=[g.id for g in groups],
                group_size=total_size,
                is_lab=alloc.course.has_lab and i == n_sessions - 1,
                required_equipment=list(alloc.course.requires_equipment or []),
                allowed_days=[5] if alloc.course.programme.level in (
                    ProgrammeLevel.MASTERS, ProgrammeLevel.PHD,
                ) else [0, 1, 2, 3, 4],
            ))
            sid_to_alloc[sid] = alloc
        for g in groups:
            cap = _max_days_for_level_semester(alloc.course.programme.level, semester.number)
            max_days_per_group[g.id] = cap

    rooms = list(Room.objects.filter(is_active=True).prefetch_related("equipment"))
    room_inputs = [
        RoomInput(
            id=r.id, capacity=r.capacity, room_type=r.room_type,
            equipment=list(r.equipment.values_list("code", flat=True)),
        ) for r in rooms
    ]

    slot_qs = TimeSlot.objects.filter(is_lunch=False).order_by("order")
    slot_ids = list(slot_qs.values_list("id", flat=True))

    # weekdays + saturday (PG)
    days = [0, 1, 2, 3, 4, 5]

    solver = TimetableSolver(
        sessions=sessions, rooms=room_inputs, slot_ids=slot_ids,
        days=days, max_days_per_group=max_days_per_group,
        time_limit_seconds=time_limit_seconds,
    )
    result = solver.solve()

    with transaction.atomic():
        version = (Timetable.objects.filter(semester=semester).order_by("-version").values_list("version", flat=True).first() or 0) + 1
        tt = Timetable.objects.create(
            semester=semester, name=name, version=version,
            status=TimetableStatus.READY if result.assignments else TimetableStatus.DRAFT,
            optimization_score=result.objective,
            hard_violations=result.hard_violations,
            soft_violations=result.soft_violations,
            generated_by_id=user_id,
            notes="\n".join(result.log),
        )
        for a in result.assignments:
            alloc = sid_to_alloc[a["session_id"]]
            entry = TimetableEntry.objects.create(
                timetable=tt, course=alloc.course, lecturer=alloc.lecturer,
                room_id=a["room_id"], day=a["day"], time_slot_id=a["slot_id"],
                is_lab=alloc.course.has_lab,
            )
            entry.student_groups.set(alloc.student_groups.all())
    return tt
