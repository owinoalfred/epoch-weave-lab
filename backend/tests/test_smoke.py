import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_user_role_assignment():
    from apps.accounts.models import UserRole, Role
    u = User.objects.create_user(username="t", email="t@x.io", password="pw12345!")
    UserRole.objects.create(user=u, role=Role.LECTURER)
    assert u.has_role(Role.LECTURER)


@pytest.mark.django_db
def test_lecturer_max_hours():
    from apps.staff.models import LecturerRank
    assert LecturerRank.max_hours(LecturerRank.LECTURER) == 22
    assert LecturerRank.max_hours(LecturerRank.HOD) == 16
    assert LecturerRank.max_hours(LecturerRank.DEAN) == 12
    assert LecturerRank.max_hours(LecturerRank.LAB_ASSISTANT) == 12
