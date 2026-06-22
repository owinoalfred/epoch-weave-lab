from django.db import models

class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"

class TimeSlot(models.Model):
    """Canonical teaching time slot."""
    name = models.CharField(max_length=32)
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveSmallIntegerField(default=0)
    is_lunch = models.BooleanField(default=False) # 1:00 PM - 2:00 PM block

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"

class TimetableStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    GENERATING = "GENERATING", "Generating"
    PUBLISHED = "PUBLISHED", "Published"

class Timetable(models.Model):
    name = models.CharField(max_length=160)
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.CASCADE, related_name="timetables")
    semester = models.ForeignKey("academics.Semester", on_delete=models.CASCADE, related_name="timetables")
    term = models.ForeignKey("academics.Term", on_delete=models.CASCADE, null=True, blank=True, related_name="timetables")
    status = models.CharField(max_length=16, choices=TimetableStatus.choices, default=TimetableStatus.DRAFT)
    generated_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.status}]"

class TimetableEntry(models.Model):
    """A single scheduled session in the generated timetable."""
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name="entries")
    course = models.ForeignKey("academics.Course", on_delete=models.CASCADE)
    student_group = models.ForeignKey("academics.StudentGroup", on_delete=models.CASCADE)
    lecturer = models.ForeignKey("staff.Lecturer", on_delete=models.CASCADE)
    room = models.ForeignKey("facilities.Room", on_delete=models.CASCADE)
    day = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "day", "time_slot"], name="unique_room_slot"),
            models.UniqueConstraint(fields=["lecturer", "day", "time_slot"], name="unique_lecturer_slot"),
            models.UniqueConstraint(fields=["student_group", "day", "time_slot"], name="unique_group_slot"),
        ]

    def __str__(self):
        return f"{self.course.code} - {self.get_day_display()} {self.time_slot}"

class RoomBooking(models.Model):
    """Ad-hoc room booking outside the auto-generated timetable."""
    room = models.ForeignKey("facilities.Room", on_delete=models.CASCADE, related_name="bookings")
    booked_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    purpose = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "start_time"]

    def __str__(self):
        return f"{self.room.code} - {self.date} ({self.start_time} to {self.end_time})"