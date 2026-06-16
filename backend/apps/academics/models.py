from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AcademicYear(TimeStamped):
    name = models.CharField(max_length=32, unique=True)  # e.g. 2025/2026
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    def __str__(self): return self.name


class Faculty(TimeStamped):
    name = models.CharField(max_length=160, unique=True)
    code = models.CharField(max_length=16, unique=True)
    dean = models.ForeignKey("accounts.User", null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="deans_of")

    class Meta:
        verbose_name_plural = "Faculties"
        ordering = ["name"]

    def __str__(self): return self.name


class Department(TimeStamped):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=16)
    hod = models.ForeignKey("accounts.User", null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="hod_of")

    class Meta:
        unique_together = [("faculty", "code")]
        ordering = ["name"]

    def __str__(self): return f"{self.faculty.code}/{self.code} — {self.name}"


class ProgrammeLevel(models.TextChoices):
    UNDERGRADUATE = "UG", "Undergraduate"
    MASTERS = "MS", "Masters"
    PHD = "PHD", "PhD"
    POSTGRAD = "PG", "Postgraduate"


class Programme(TimeStamped):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="programmes")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=24)
    level = models.CharField(max_length=4, choices=ProgrammeLevel.choices)
    duration_years = models.PositiveSmallIntegerField(default=3)

    class Meta:
        unique_together = [("department", "code")]
        ordering = ["name"]

    def __str__(self): return f"{self.code} — {self.name}"


class Semester(TimeStamped):
    """A semester instance within an academic year."""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="semesters")
    name = models.CharField(max_length=64)  # Semester 1 / 2
    number = models.PositiveSmallIntegerField()  # 1, 2
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = [("academic_year", "number")]
        ordering = ["academic_year", "number"]

    def __str__(self): return f"{self.academic_year.name} {self.name}"


class Term(TimeStamped):
    """Undergraduate terms within a semester (Term 1, Term 2)."""
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="terms")
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = [("semester", "number")]
        ordering = ["semester", "number"]

    def __str__(self): return f"{self.semester} Term {self.number}"


class Course(TimeStamped):
    """Course Unit."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="courses")
    code = models.CharField(max_length=24)
    title = models.CharField(max_length=240)
    credit_units = models.PositiveSmallIntegerField(default=3)
    weekly_hours = models.PositiveSmallIntegerField(default=3,
        help_text="Total contact hours per week (lecture + lab)")
    has_lab = models.BooleanField(default=False)
    requires_equipment = models.JSONField(default=list, blank=True,
        help_text="List of required equipment codes (e.g. ['computers','projector']).")
    year_of_study = models.PositiveSmallIntegerField(default=1)
    semester_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = [("programme", "code")]
        ordering = ["code"]
        indexes = [models.Index(fields=["code"]), models.Index(fields=["year_of_study"])]

    def __str__(self): return f"{self.code} — {self.title}"


class StudentGroup(TimeStamped):
    """Cohort of students (e.g. BSc CS Year 2 Group A)."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="student_groups")
    name = models.CharField(max_length=120)
    year_of_study = models.PositiveSmallIntegerField()
    size = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("programme", "name", "year_of_study")]
        ordering = ["programme", "year_of_study", "name"]

    def __str__(self): return f"{self.programme.code} Y{self.year_of_study} {self.name}"


class Holiday(TimeStamped):
    date = models.DateField(unique=True)
    name = models.CharField(max_length=160)
