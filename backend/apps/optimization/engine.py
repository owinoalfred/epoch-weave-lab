import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model
from django.db.models import Q

from apps.academics.models import Semester, Term, Course, StudentGroup, ProgrammeLevel
from apps.staff.models import Lecturer, CourseAllocation
from apps.facilities.models import Room
from apps.scheduling.models import TimeSlot, Timetable, TimetableEntry, DayOfWeek

logger = logging.getLogger(__name__)

@dataclass
class RoomInput:
    id: int
    code: str
    capacity: int
    is_lab: bool

@dataclass
class SessionInput:
    id: int
    course_id: int
    group_id: int
    lecturer_id: int
    hours_per_week: int
    requires_lab: bool
    programme_level: str
    semester_number: int

class TimetableSolver:
    """
    OR-Tools CP-SAT Solver for University Timetabling.
    Enforces constraints:
    - Lecturer Weekly Load: 22h (11 slots), 16h (8 slots), 12h (6 slots)
    - Lecturer Daily Load: Max 6h (3 slots)
    - Student Days: Sem 1 = 4 days, Others = 3 days
    - Masters/Postgrad: Saturday only
    - Lunch Block: 1:00 PM - 2:00 PM blocked
    - Soft: Minimize gaps between classes
    """

    def __init__(self, semester_id: int, term_id: Optional[int] = None):
        self.semester_id = semester_id
        self.term_id = term_id
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        # Data containers
        self.rooms: List[RoomInput] = []
        self.sessions: List[SessionInput] = []
        self.slots: List[TimeSlot] = []
        self.lecturers: Dict[int, Lecturer] = {}
        self.groups: Dict[int, StudentGroup] = {}
        
        # Decision variables
        self.x = {}

    def load_data(self):
        """Fetch all necessary data from Django ORM."""
        logger.info("Loading data for semester %s...", self.semester_id)
        
        # 1. Load Rooms
        for room in Room.objects.filter(is_active=True, is_physical=True):
            self.rooms.append(RoomInput(
                id=room.id,
                code=room.code,
                capacity=room.capacity,
                is_lab=(room.room_type == 'lab')
            ))

        # 2. Load Time Slots (Exclude Lunch)
        self.slots = list(TimeSlot.objects.filter(is_lunch=False).order_by('order'))

        # 3. Load Lecturers
        for lec in Lecturer.objects.filter(is_active=True):
            self.lecturers[lec.id] = lec

        # 4. Load Student Groups
        semester = Semester.objects.get(id=self.semester_id)
        for group in StudentGroup.objects.filter(semester=semester):
            self.groups[group.id] = group

        # 5. Load Courses and Allocations (Sessions)
        # Filter courses by term if it's an undergrad semester
        courses_q = Course.objects.filter(semester=semester)
        if self.term_id:
            courses_q = courses_q.filter(term_id=self.term_id)
        else:
            # Masters/Postgrad: ignore term
            courses_q = courses_q.filter(term__isnull=True)

        allocations = CourseAllocation.objects.filter(
            course__in=courses_q, 
            academic_year=semester.academic_year
        ).select_related('course', 'lecturer')

        for alloc in allocations:
            course = alloc.course
            group = self.groups.get(alloc.course.programme.student_groups.filter(semester=semester).first().id) if alloc.course.programme.student_groups.filter(semester=semester).exists() else None
            
            if not group:
                continue

            self.sessions.append(SessionInput(
                id=alloc.id,
                course_id=course.id,
                group_id=group.id,
                lecturer_id=alloc.lecturer_id,
                hours_per_week=course.hours_per_week,
                requires_lab=course.requires_lab,
                programme_level=course.programme.level,
                semester_number=group.semester_number
            ))

    def build_model(self):
        """Build the CP-SAT model with all constraints."""
        logger.info("Building OR-Tools model...")
        
        # Create Boolean Variables
        # x[(session_idx, room_id, day, slot_id)] = 1 if scheduled
        for i, session in enumerate(self.sessions):
            for room in self.rooms:
                # Room Capacity Constraint
                if room.capacity < self.groups[session.group_id].head_count:
                    continue
                # Room Type Constraint (Lab)
                if session.requires_lab and not room.is_lab:
                    continue

                for day in range(7): # 0=Mon, 5=Sat, 6=Sun
                    # MASTERS/POSTGRAD CONSTRAINT: Only Saturdays
                    if session.programme_level in [ProgrammeLevel.MASTERS, ProgrammeLevel.POSTGRAD]:
                        if day != DayOfWeek.SATURDAY:
                            continue
                    
                    # UNDERGRAD CONSTRAINT: No Sundays
                    if day == DayOfWeek.SUNDAY:
                        continue

                    for slot in self.slots:
                        var_name = f"x_{i}_{room.id}_{day}_{slot.id}"
                        self.x[(i, room.id, day, slot.id)] = self.model.NewBoolVar(var_name)

        # --- HARD CONSTRAINTS ---

        # 1. Each session must be scheduled exactly (hours_per_week / 2) times
        # Assuming 1 slot = 2 hours.
        session_indices = {}
        for i, session in enumerate(self.sessions):
            session_indices.setdefault(session.course_id, []).append(i)
            required_slots = max(1, session.hours_per_week // 2)
            vars_for_session = [self.x[(i, r.id, d, s.id)] for (idx, r_id, d, s_id) in self.x if idx == i]
            self.model.Add(sum(vars_for_session) == required_slots)

        # 2. No Room Clashes
        for room in self.rooms:
            for day in range(7):
                for slot in self.slots:
                    vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x if r_id == room.id and d == day and s_id == slot.id]
                    if vars_list:
                        self.model.Add(sum(vars_list) <= 1)

        # 3. No Lecturer Clashes
        for lec_id in self.lecturers.keys():
            for day in range(7):
                for slot in self.slots:
                    vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                                 if self.sessions[idx].lecturer_id == lec_id and d == day and s_id == slot.id]
                    if vars_list:
                        self.model.Add(sum(vars_list) <= 1)

        # 4. No Group Clashes
        for grp_id in self.groups.keys():
            for day in range(7):
                for slot in self.slots:
                    vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                                 if self.sessions[idx].group_id == grp_id and d == day and s_id == slot.id]
                    if vars_list:
                        self.model.Add(sum(vars_list) <= 1)

        # 5. Lecturer Weekly Load (22h=11, 16h=8, 12h=6)
        for lec_id, lecturer in self.lecturers.items():
            max_slots = lecturer.max_weekly_slots
            vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                         if self.sessions[idx].lecturer_id == lec_id]
            if vars_list:
                self.model.Add(sum(vars_list) <= max_slots)

        # 6. Lecturer Daily Load (Max 6h = 3 slots)
        for lec_id, lecturer in self.lecturers.items():
            max_daily = lecturer.max_daily_slots
            for day in range(7):
                vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                             if self.sessions[idx].lecturer_id == lec_id and d == day]
                if vars_list:
                    self.model.Add(sum(vars_list) <= max_daily)

        # 7. Student Days Per Week (Sem 1 = 4 days, Others = 3 days)
        for grp_id, group in self.groups.items():
            max_days = group.max_days_per_week
            day_used = {day: self.model.NewBoolVar(f'day_used_{grp_id}_{day}') for day in range(7)}
            
            for day in range(7):
                vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                             if self.sessions[idx].group_id == grp_id and d == day]
                if vars_list:
                    self.model.AddMaxEquality(day_used[day], vars_list)
                    
            self.model.Add(sum(day_used.values()) <= max_days)

        # --- SOFT CONSTRAINTS (Minimize Gaps) ---
        penalties = []
        for grp_id in self.groups.keys():
            for day in range(7):
                for i in range(len(self.slots) - 2):
                    s1, s2, s3 = self.slots[i], self.slots[i+1], self.slots[i+2]
                    # Gap allowed during lunch, but we already filtered lunch slots out.
                    # If s2 is missing in the list, it might be lunch, so we skip.
                    
                    vars_s1 = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x if self.sessions[idx].group_id == grp_id and d == day and s_id == s1.id]
                    vars_s3 = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x if self.sessions[idx].group_id == grp_id and d == day and s_id == s3.id]
                    vars_s2 = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x if self.sessions[idx].group_id == grp_id and d == day and s_id == s2.id]

                    if vars_s1 and vars_s3 and vars_s2:
                        gap = self.model.NewBoolVar(f'gap_{grp_id}_{day}_{s1.id}')
                        self.model.AddBoolAnd([vars_s1[0], vars_s3[0]]).OnlyEnforceIf(gap)
                        penalties.append(gap * 10)

        if penalties:
            self.model.Minimize(sum(penalties))

    def solve(self, timeout_seconds: int = 120) -> bool:
        """Run the solver."""
        logger.info("Starting solver...")
        self.solver.parameters.max_time_in_seconds = timeout_seconds
        
        status = self.solver.Solve(self.model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.info("Solver found a solution!")
            return True
        else:
            logger.error("Solver failed to find a solution. Status: %s", status)
            return False

    def save_results(self, timetable: Timetable):
        """Save the solver's output to the database."""
        logger.info("Saving results to database...")
        TimetableEntry.objects.filter(timetable=timetable).delete()
        
        for (idx, room_id, day, slot_id), var in self.x.items():
            if self.solver.Value(var) == 1:
                session = self.sessions[idx]
                TimetableEntry.objects.create(
                    timetable=timetable,
                    course_id=session.course_id,
                    student_group_id=session.group_id,
                    lecturer_id=session.lecturer_id,
                    room_id=room_id,
                    day=day,
                    time_slot_id=slot_id
                )