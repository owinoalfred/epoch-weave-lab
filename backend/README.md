# UniTime — Django Backend

Production-ready Django + DRF + PostgreSQL + Redis + Celery + OR-Tools backend
for the University Timetabling and Scheduling Management Platform.

## Stack
- Python 3.11, Django 5, Django REST Framework
- PostgreSQL 16, Redis 7
- Celery 5 (background timetable generation)
- Google OR-Tools (CP-SAT constraint solver)
- SimpleJWT (auth), drf-spectacular (OpenAPI)
- Docker + docker-compose

## Quickstart (Docker)

```bash
cd backend
cp .env.example .env
docker compose up --build
# In another shell:
docker compose exec api python manage.py migrate
docker compose exec api python manage.py createsuperuser
docker compose exec api python manage.py seed_demo   # optional
```

API: http://localhost:8000/api/
OpenAPI: http://localhost:8000/api/docs/
Admin:   http://localhost:8000/admin/

## Local (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgres://unitime:unitime@localhost:5432/unitime
export REDIS_URL=redis://localhost:6379/0
python manage.py migrate
python manage.py runserver
celery -A unitime worker -l info
```

## Apps
- `accounts` — users, roles, JWT auth
- `academics` — faculties, departments, programmes, semesters, terms, courses, student groups
- `facilities` — rooms, equipment
- `staff` — lecturers, workloads
- `scheduling` — timetables, entries, room bookings, versioning, approvals
- `optimization` — OR-Tools CP-SAT engine + Celery tasks
- `analytics` — reports (workload, utilization, clashes)
- `audit` — audit logs, notifications

## CORS
Set `CORS_ALLOWED_ORIGINS` in `.env` to your frontend URL.

## Tests
```bash
pytest
```
