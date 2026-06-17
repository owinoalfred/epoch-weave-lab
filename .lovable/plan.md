
## Why `admin / admin12345` doesn't log you in

Those credentials are real — but they only exist **after** you run the Django backend and execute:

```bash
docker compose exec api python manage.py migrate
docker compose exec api python manage.py seed_demo
```

The Lovable preview cannot reach `http://localhost:8000/api` from your browser, so the login POST fails with a network error and you see "Invalid credentials". Nothing is wrong with the password — there is simply no backend listening at `VITE_API_URL` from the preview sandbox.

You have two paths. Pick one (or both) and I'll build it:

### Option A — Ship a "Demo Mode" so the preview is fully usable without Django
Add a `VITE_DEMO_MODE` flag (on by default in the Lovable preview, off when you set `VITE_API_URL`). When on:
- `api.ts` routes every request to an in-browser mock layer (seeded with the same faculties/departments/programmes/courses/rooms/lecturers as `seed_demo.py`, persisted to `localStorage`)
- `admin / admin12345` logs in instantly and issues a fake JWT
- The TS-side timetable generator runs a lightweight CP/greedy solver so you can see generated schedules end-to-end
- When you deploy your Django backend and set `VITE_API_URL`, the mock layer turns off automatically and everything talks to real DRF

### Option B — Finish the remaining product features (frontend + matching Django endpoints)
Already shipped: schema, JWT auth, CRUD for all academic entities, dashboard, timetable viewer, generator trigger, OR-Tools engine, Celery wiring, seed data, Docker, OpenAPI.

Remaining work to call it "complete":

**Frontend**
1. Drag-and-drop timetable editor (manual overrides, live clash highlighting) using `@dnd-kit`
2. Export menu on a published timetable: PDF (jsPDF + autotable), Excel (xlsx), CSV, ICS calendar feed per lecturer/group/room
3. Notifications panel (bell icon, unread badge, mark-as-read) backed by `/api/notifications`
4. Approval workflow UI: Draft → Submitted → Approved/Rejected with comments, version diff view
5. Granular RBAC gating in the sidebar + route guards (Dean / HOD / Timetable Officer / Lecturer / Student views)
6. Lecturer "My Schedule" + Student Group "My Schedule" read-only pages
7. Conflict report page (room double-bookings, lecturer overloads, equipment mismatches) with filters
8. Analytics page upgrade: workload distribution, room utilization heatmap, peak-hour chart, unscheduled-course list
9. Settings: time slots editor, working days, constraint weights (gap penalty, day-cap), academic-year switcher
10. Empty states, skeletons, optimistic mutations, toasts wired to React Query everywhere
11. Polished login page with role hint card + branded landing/`/about` route

**Backend (Django)**
1. `notifications` app (model + DRF viewset + signal emitters on timetable status changes)
2. `scheduling` workflow endpoints: `submit/`, `approve/`, `reject/`, `publish/`, version snapshot table
3. Export endpoints: `timetables/{id}/export.pdf|xlsx|csv|ics` (ReportLab + openpyxl + ics)
4. `conflicts/` endpoint that re-runs the validator and returns structured issues
5. Analytics endpoints: `/analytics/workload`, `/analytics/utilization`, `/analytics/peak-hours`
6. Permission classes per role using `UserRole` (Dean/HOD scope filters)
7. Audit log viewset + middleware coverage for all write operations
8. Solver hardening: equipment matching, lab vs lecture room separation, lecturer unavailability windows, soft-constraint weights from Settings
9. Pytest coverage for solver (feasible/infeasible cases) + API smoke tests for each viewset
10. GitHub Actions: lint (ruff) + pytest + docker build

### Recommended path
**Do both: A then B.** Demo Mode lets you actually click through the finished product in the Lovable preview today; Option B then layers in every remaining feature against both the mock and the real Django API so nothing diverges.

### Question before I start
Confirm "Do both, in that order" — or tell me to skip Demo Mode and only ship Option B (in which case you'll need to run the Django stack locally to see anything beyond the login screen).
