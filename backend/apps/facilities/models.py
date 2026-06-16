from django.db import models


class RoomType(models.TextChoices):
    LECTURE = "LECTURE", "Lecture Room"
    LAB = "LAB", "Laboratory"
    COMPUTER_LAB = "COMPUTER_LAB", "Computer Lab"
    SEMINAR = "SEMINAR", "Seminar Room"
    AUDITORIUM = "AUDITORIUM", "Auditorium"


class Equipment(models.Model):
    code = models.SlugField(max_length=32, unique=True)  # computers, projector, internet
    name = models.CharField(max_length=80)

    def __str__(self): return self.name


class Room(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=160)
    building = models.CharField(max_length=120)
    floor = models.CharField(max_length=16, blank=True)
    capacity = models.PositiveIntegerField()
    room_type = models.CharField(max_length=16, choices=RoomType.choices, default=RoomType.LECTURE)
    equipment = models.ManyToManyField(Equipment, blank=True, related_name="rooms")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["building", "code"]
        indexes = [models.Index(fields=["room_type"]), models.Index(fields=["capacity"])]

    def __str__(self): return f"{self.code} ({self.building})"
