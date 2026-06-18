from django.db import models

class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True) # e.g., "2026/2027"
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Faculty(models.Model):
    """e.g., Faculty of Computing, Faculty of Engineering"""
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="departments")
    hod = models.ForeignKey("staff.Lecturer", on_delete=models.SET_NULL, null=True, blank=True, related_name="hod_departments")

    def __str__(self):
        return self.name

# --- ADDED THIS BACK AS A STANDALONE CLASS ---
class ProgrammeLevel(models.TextChoices):
    UNDERGRAD = "UNDERGRAD", "Undergraduate"
    MASTERS = "MASTERS", "Masters"
    POSTGRAD = "POSTGRAD", "Postgraduate"

class Programme(models.Model):
    """e.g., BSCAIT, MBA, MSCIT"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    
    # Use the standalone ProgrammeLevel class
    level = models.CharField(max_length=20, choices=ProgrammeLevel.choices, default=ProgrammeLevel.UNDERGRAD)
    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="programmes")
    total_semesters = models.PositiveSmallIntegerField(default=8)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="semesters")
    number = models.PositiveSmallIntegerField() # 1, 2
    name = models.CharField(max_length=50) # e.g., "Semester 1"

    class Meta:
        unique_together = [("academic_year", "number")]
        ordering = ["number"]

    def __str__(self):
        return f"{self.academic_year.name} - {self.name}"

class Term(models.Model):
    """Undergrad semesters are split into Term 1 and Term 2. Masters have no terms."""
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="terms")
    number = models.PositiveSmallIntegerField() # 1 or 2
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = [("semester", "number")]

    def __str__(self):
        return f"{self.semester} - {self.name}"

class Course(models.Model):
    """A specific course unit (e.g., Internet of Things)."""
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="courses")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="courses")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True, related_name="courses")
    hours_per_week = models.PositiveSmallIntegerField(default=2)
    requires_lab = models.BooleanField(default=False)

    class Meta:
        unique_together = [("code", "programme", "semester", "term")]

    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentGroup(models.Model):
    """A specific cohort/batch (e.g., BSCAITS24DA)."""
    code = models.CharField(max_length=50, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name="student_groups")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="student_groups")
    head_count = models.PositiveIntegerField(default=30)
    semester_number = models.PositiveSmallIntegerField(default=1) # Used for day constraints

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code

    @property
    def max_days_per_week(self):
        """Semester 1 gets 4 days, others get 3 days."""
        return 4 if self.semester_number == 1 else 3

class Holiday(models.Model):
    """University holidays where no classes are held."""
    name = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} ({self.date})"