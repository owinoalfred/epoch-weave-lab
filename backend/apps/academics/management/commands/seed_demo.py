"""Seed minimal demo data: faculty -> department -> programme -> course -> lecturer -> rooms -> slots."""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import time, date
from apps.academics.models import (
    AcademicYear, Faculty, Department, Programme, ProgrammeLevel,
    Semester, Course, StudentGroup,
)
from apps.staff.models import Lecturer, LecturerRank, CourseAllocation
from apps.facilities.models import Room, RoomType, Equipment
from apps.scheduling.models import TimeSlot

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data"

    def handle(self, *args, **opts):
        ay, _ = AcademicYear.objects.get_or_create(
            name="2025/2026",
            defaults=dict(start_date=date(2025, 8, 1), end_date=date(2026, 7, 31), is_active=True),
        )
        sem, _ = Semester.objects.get_or_create(
            academic_year=ay, number=1,
            defaults=dict(name="Semester 1", start_date=date(2025, 8, 15),
                          end_date=date(2025, 12, 15), is_active=True),
        )

        # Time slots
        slots = [
            ("Slot 1", time(9, 0), time(10, 55), 1, False),
            ("Slot 2", time(11, 0), time(13, 0), 2, False),
            ("Lunch",  time(13, 0), time(14, 0), 3, True),
            ("Slot 3", time(14, 0), time(15, 55), 4, False),
            ("Slot 4", time(16, 0), time(18, 0), 5, False),
        ]
        for name, s, e, o, lunch in slots:
            TimeSlot.objects.get_or_create(name=name, defaults=dict(
                start_time=s, end_time=e, order=o, is_lunch=lunch))

        fac, _ = Faculty.objects.get_or_create(code="FOC", defaults=dict(name="Faculty of Computing"))
        dept, _ = Department.objects.get_or_create(faculty=fac, code="CS", defaults=dict(name="Computer Science"))
        prog, _ = Programme.objects.get_or_create(department=dept, code="BSCCS",
            defaults=dict(name="BSc Computer Science", level=ProgrammeLevel.UNDERGRADUATE, duration_years=3))

        # Equipment
        for code, name in [("computers", "Computers"), ("projector", "Projector"), ("internet", "Internet")]:
            Equipment.objects.get_or_create(code=code, defaults=dict(name=name))

        # Rooms
        lec1, _ = Room.objects.get_or_create(code="LR-101", defaults=dict(
            name="Lecture Room 101", building="Block A", floor="1",
            capacity=120, room_type=RoomType.LECTURE))
        lec2, _ = Room.objects.get_or_create(code="LR-102", defaults=dict(
            name="Lecture Room 102", building="Block A", floor="1",
            capacity=80, room_type=RoomType.LECTURE))
        lab1, _ = Room.objects.get_or_create(code="CLAB-01", defaults=dict(
            name="Computer Lab 1", building="Block B", floor="G",
            capacity=40, room_type=RoomType.COMPUTER_LAB))
        for eq_code in ("computers", "projector", "internet"):
            lab1.equipment.add(Equipment.objects.get(code=eq_code))
        lec1.equipment.add(Equipment.objects.get(code="projector"))

        # Courses
        c1, _ = Course.objects.get_or_create(programme=prog, code="CS101",
            defaults=dict(title="Intro to Programming", credit_units=4, weekly_hours=4, has_lab=True,
                          requires_equipment=["computers"], year_of_study=1, semester_number=1))
        c2, _ = Course.objects.get_or_create(programme=prog, code="CS102",
            defaults=dict(title="Discrete Math", credit_units=3, weekly_hours=3, year_of_study=1, semester_number=1))

        # Lecturer
        u, _ = User.objects.get_or_create(username="jdoe", defaults=dict(
            email="jdoe@uni.edu", first_name="Jane", last_name="Doe"))
        if not u.has_usable_password():
            u.set_password("password123"); u.save()
        lec, _ = Lecturer.objects.get_or_create(user=u, defaults=dict(
            staff_no="STF001", department=dept, rank=LecturerRank.LECTURER, title="Dr."))

        # Student group
        g1, _ = StudentGroup.objects.get_or_create(programme=prog, name="Group A", year_of_study=1,
            defaults=dict(size=60))

        # Allocations
        a1, _ = CourseAllocation.objects.get_or_create(lecturer=lec, course=c1, semester=sem)
        a1.student_groups.add(g1)
        a2, _ = CourseAllocation.objects.get_or_create(lecturer=lec, course=c2, semester=sem)
        a2.student_groups.add(g1)

        # Admin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(username="admin", email="admin@uni.edu", password="admin12345")
            self.stdout.write(self.style.SUCCESS("Created superuser admin/admin12345"))

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
