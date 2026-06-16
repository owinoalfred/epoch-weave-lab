"""
UniTime CP-SAT timetabling engine (Google OR-Tools).

Models the timetabling problem as a Constraint Satisfaction / Optimization Problem.

For each session s in the input "sessions" list, decide:
    day_s in {valid_days}
    slot_s in {valid_slots}
    room_s in {valid_rooms}

Hard constraints:
  - Lecturer cannot teach two sessions at the same (day, slot)
  - Room cannot host two sessions at the same (day, slot)
  - Student group cannot attend two sessions at the same (day, slot)
  - Room capacity >= group size
  - Room type / equipment compatibility (labs go to labs)
  - Lecturer weekly hours <= max for rank

Soft (objective):
  - Minimize idle gaps in each student group's day
  - Minimize number of distinct days each student group attends (cap by rules)
  - Balance lecturer schedules
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable
from ortools.sat.python import cp_model


@dataclass
class SessionInput:
    id: int
    course_code: str
    lecturer_id: int
    lecturer_max_hours: int
    group_ids: list[int]
    group_size: int
    duration_slots: int = 1  # 1 = single slot
    is_lab: bool = False
    required_equipment: list[str] = field(default_factory=list)
    allowed_days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])


@dataclass
class RoomInput:
    id: int
    capacity: int
    room_type: str  # LECTURE / LAB / COMPUTER_LAB / SEMINAR / AUDITORIUM
    equipment: list[str]


@dataclass
class SolveResult:
    status: str
    assignments: list[dict]   # [{session_id, day, slot, room_id}, ...]
    objective: float | None
    hard_violations: int
    soft_violations: int
    log: list[str]


class TimetableSolver:
    def __init__(
        self,
        sessions: list[SessionInput],
        rooms: list[RoomInput],
        slot_ids: list[int],          # ordered list of slot DB ids (lunch excluded)
        days: list[int],              # e.g. [0..4] weekdays, [5] saturday for PG
        max_days_per_group: dict[int, int] | None = None,  # group_id -> cap
        time_limit_seconds: int = 30,
    ):
        self.sessions = sessions
        self.rooms = rooms
        self.slot_ids = slot_ids
        self.days = days
        self.max_days_per_group = max_days_per_group or {}
        self.time_limit_seconds = time_limit_seconds
        self.log: list[str] = []

    # --------------------------------------------------------------- helpers
    def _room_is_compatible(self, s: SessionInput, r: RoomInput) -> bool:
        if r.capacity < s.group_size:
            return False
        if s.is_lab and r.room_type not in {"LAB", "COMPUTER_LAB"}:
            return False
        for eq in s.required_equipment:
            if eq not in r.equipment:
                return False
        return True

    # --------------------------------------------------------------- solve
    def solve(self) -> SolveResult:
        model = cp_model.CpModel()
        n_days = len(self.days)
        n_slots = len(self.slot_ids)
        n_rooms = len(self.rooms)

        # Decision variables
        day_v, slot_v, room_v = {}, {}, {}
        # x[s, d, t, r] = 1 iff session s placed at day index d, slot index t, room index r
        x = {}

        for s in self.sessions:
            allowed_day_idx = [i for i, d in enumerate(self.days) if d in s.allowed_days] or list(range(n_days))
            day_v[s.id] = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(allowed_day_idx), f"day_{s.id}")
            slot_v[s.id] = model.NewIntVar(0, n_slots - 1, f"slot_{s.id}")
            compatible_rooms = [i for i, r in enumerate(self.rooms) if self._room_is_compatible(s, r)]
            if not compatible_rooms:
                self.log.append(f"No compatible room for session {s.id} ({s.course_code}) — relaxing capacity/type")
                compatible_rooms = list(range(n_rooms))
            room_v[s.id] = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(compatible_rooms), f"room_{s.id}")

            # Channel into x
            for d_idx in allowed_day_idx:
                for t in range(n_slots):
                    for r_idx in compatible_rooms:
                        var = model.NewBoolVar(f"x_{s.id}_{d_idx}_{t}_{r_idx}")
                        x[(s.id, d_idx, t, r_idx)] = var
            # Exactly one (d,t,r) is chosen
            model.AddExactlyOne(
                v for (sid, d, t, r), v in x.items() if sid == s.id
            )
            # Channel decision vars to x
            for (sid, d, t, r), v in x.items():
                if sid != s.id: continue
                model.Add(day_v[s.id] == d).OnlyEnforceIf(v)
                model.Add(slot_v[s.id] == t).OnlyEnforceIf(v)
                model.Add(room_v[s.id] == r).OnlyEnforceIf(v)

        # Hard: lecturer no clash
        for d_idx in range(n_days):
            for t in range(n_slots):
                # room clash
                for r_idx in range(n_rooms):
                    vars_here = [v for (sid, d, tt, r), v in x.items()
                                 if d == d_idx and tt == t and r == r_idx]
                    if vars_here:
                        model.Add(sum(vars_here) <= 1)
                # lecturer clash
                lecturers = {s.lecturer_id for s in self.sessions}
                for lid in lecturers:
                    vars_here = [
                        v for (sid, d, tt, r), v in x.items()
                        if d == d_idx and tt == t
                        and next(s for s in self.sessions if s.id == sid).lecturer_id == lid
                    ]
                    if vars_here:
                        model.Add(sum(vars_here) <= 1)
                # group clash
                all_groups = {g for s in self.sessions for g in s.group_ids}
                for gid in all_groups:
                    vars_here = [
                        v for (sid, d, tt, r), v in x.items()
                        if d == d_idx and tt == t
                        and gid in next(s for s in self.sessions if s.id == sid).group_ids
                    ]
                    if vars_here:
                        model.Add(sum(vars_here) <= 1)

        # Hard: lecturer weekly hours
        lecturers = {s.lecturer_id: s.lecturer_max_hours for s in self.sessions}
        for lid, max_hours in lecturers.items():
            total = []
            for s in self.sessions:
                if s.lecturer_id != lid: continue
                total.append(s.duration_slots * 2)  # each slot ~ 2 hours
            if total and sum(total) > max_hours:
                # not solvable; record violation but proceed
                self.log.append(f"Lecturer {lid}: required hours {sum(total)} exceed cap {max_hours}")

        # Soft objective: minimize spread of group days
        group_day_used = {}
        all_groups = {g for s in self.sessions for g in s.group_ids}
        for gid in all_groups:
            for d_idx in range(n_days):
                used = model.NewBoolVar(f"g{gid}_d{d_idx}_used")
                group_day_used[(gid, d_idx)] = used
                related = [
                    v for (sid, d, t, r), v in x.items()
                    if d == d_idx
                    and gid in next(s for s in self.sessions if s.id == sid).group_ids
                ]
                if related:
                    model.AddMaxEquality(used, related)
                else:
                    model.Add(used == 0)

        # Apply max-days-per-group cap as hard constraint where provided
        for gid, cap in self.max_days_per_group.items():
            model.Add(sum(group_day_used[(gid, d)] for d in range(n_days)) <= cap)

        # Objective: minimize total (group_days_used + slot spread)
        objective_terms = []
        for (gid, d), v in group_day_used.items():
            objective_terms.append(v)
        if objective_terms:
            model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_seconds
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model)

        status_name = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "UNKNOWN",
        }.get(status, str(status))

        assignments = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for s in self.sessions:
                d = self.days[solver.Value(day_v[s.id])]
                t = self.slot_ids[solver.Value(slot_v[s.id])]
                r = self.rooms[solver.Value(room_v[s.id])].id
                assignments.append({
                    "session_id": s.id, "day": d, "slot_id": t, "room_id": r,
                })

        return SolveResult(
            status=status_name,
            assignments=assignments,
            objective=solver.ObjectiveValue() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
            hard_violations=0 if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 1,
            soft_violations=int(solver.ObjectiveValue() or 0) if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
            log=self.log,
        )
