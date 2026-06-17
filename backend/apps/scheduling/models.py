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
    """Canonical teaching time slot (M-F + Saturday for PG)."""
    name = models.CharField(max_length=32) # Slot 1, Slot 2, ...
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveSmallIntegerField(default=0)
    is_lunch = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        unique_together = [("start_time", "end_time")]

    def __str__(self): return f"{self.name} {self.start_time}-{self.end_time}"

class TimetableStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    GENERATING = "GENERATING", "Generating"
    PUBLISHED = "PUBLISHED", "Published"

class Timetable(models.Model):
    semester = models.ForeignKey("academics.Semester", on_delete=models.CASCADE, related_name="timetables")
    department = models.ForeignKey("academics.Department", null=True, blank=True,
                                   on_delete=models.CASCADE, related_name="timetables")
    name = models.CharField(max_length=160)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=TimetableStatus.choices, default=TimetableStatus.DRAFT)
    
    optimization_score = models.FloatField(null=True, blank=True)
    hard_violations = models.PositiveIntegerField(default=0)
    soft_violations = models.PositiveIntegerField(default=0)
    
    generated_by = models.ForeignKey("accounts.User", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="timetables_generated")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["semester", "status"])]

    def __str__(self): return f"{self.name} v{self.version} [{self.status}]"

class TimetableEntry(models.Model):
    """A single scheduled session."""
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name="entries")
    course = models.ForeignKey("academics.Course", on_delete=models.CASCADE)
    lecturer = models.ForeignKey("staff.Lecturer", on_delete=models.CASCADE)
    room = models.ForeignKey("facilities.Room", on_delete=models.CASCADE)
    student_groups = models.ManyToManyField("academics.StudentGroup", related_name="timetable_entries")
    day = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT)
    is_lab = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["timetable", "day"]),
            models.Index(fields=["room", "day", "time_slot"]),
            models.Index(fields=["lecturer", "day", "time_slot"]),
        ]

    def __str__(self):
        return f"{self.course.code} {self.get_day_display()} {self.time_slot}"

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