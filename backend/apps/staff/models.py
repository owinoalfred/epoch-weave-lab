from django.db import models
from django.conf import settings

class LecturerRank(models.Model):
    """Rank of the lecturer (e.g., Assistant, Associate, Full Professor)."""
    name = models.CharField(max_length=100, unique=True)
    max_hours = models.PositiveSmallIntegerField(default=22)

    def __str__(self):
        return self.name

class Lecturer(models.Model):
    """Represents a teaching staff member."""
    
    class Title(models.TextChoices):
        NORMAL = "NORMAL", "Normal Lecturer (22h/week)"
        HOD = "HOD", "Head of Department (16h/week)"
        LAB_ASSISTANT = "LAB_ASSISTANT", "Lab Assistant (12h/week)"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    
    # New field for constraints
    title = models.CharField(max_length=20, choices=Title.choices, default=Title.NORMAL)
    
    # Kept for backward compatibility with your existing serializers/views
    rank = models.ForeignKey(LecturerRank, on_delete=models.SET_NULL, null=True, blank=True, related_name="lecturers")
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_title_display()})"

    @property
    def max_weekly_slots(self):
        """
        Assuming 2-hour slots:
        22 hours = 11 slots
        16 hours = 8 slots
        12 hours = 6 slots
        """
        if self.title == self.Title.HOD:
            return 8
        if self.title == self.Title.LAB_ASSISTANT:
            return 6
        return 11  # Normal

    @property
    def max_daily_slots(self):
        """
        Max 6 hours a day = 3 slots of 2 hours each.
        """
        return 3


class CourseAllocation(models.Model):
    """Links a lecturer to a course unit."""
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name="allocations")
    course = models.ForeignKey("academics.Course", on_delete=models.CASCADE, related_name="allocations")
    academic_year = models.ForeignKey("academics.AcademicYear", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = [("lecturer", "course", "academic_year")]

    def __str__(self):
        return f"{self.lecturer.name} -> {self.course.code}"