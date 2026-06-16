from django.db import models


class LecturerRank(models.TextChoices):
    LECTURER = "LECTURER", "Lecturer"
    HOD = "HOD", "Head of Department"
    DEAN = "DEAN", "Dean"
    LAB_ASSISTANT = "LAB_ASSISTANT", "Lab Assistant"

    @classmethod
    def max_hours(cls, rank: str) -> int:
        return {
            cls.LECTURER: 22,
            cls.HOD: 16,
            cls.DEAN: 12,
            cls.LAB_ASSISTANT: 12,
        }.get(rank, 22)


class Lecturer(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="lecturer_profile")
    staff_no = models.CharField(max_length=32, unique=True)
    department = models.ForeignKey("academics.Department", on_delete=models.PROTECT, related_name="lecturers")
    rank = models.CharField(max_length=16, choices=LecturerRank.choices, default=LecturerRank.LECTURER)
    title = models.CharField(max_length=32, blank=True)  # Dr., Prof.
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["staff_no"]

    def __str__(self): return f"{self.title} {self.user.get_full_name() or self.user.username}".strip()

    @property
    def max_weekly_hours(self) -> int:
        return LecturerRank.max_hours(self.rank)


class CourseAllocation(models.Model):
    """Assigns a lecturer to teach a course in a semester."""
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name="allocations")
    course = models.ForeignKey("academics.Course", on_delete=models.CASCADE, related_name="allocations")
    semester = models.ForeignKey("academics.Semester", on_delete=models.CASCADE, related_name="allocations")
    student_groups = models.ManyToManyField("academics.StudentGroup", related_name="allocations")

    class Meta:
        unique_together = [("lecturer", "course", "semester")]
