import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from ortools.sat.python import cp_model

from apps.academics.models import Semester, Course, StudentGroup
from apps.staff.models import Lecturer, CourseAllocation
from apps.facilities.models import Room
from apps.scheduling.models import TimeSlot, Timetable, TimetableEntry, DayOfWeek

logger = logging.getLogger(__name__)

@dataclass
class RoomInput:
    id: int
    code: str
    capacity: int
    room_type: str

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
    def __init__(self, semester_id: int, term_id: Optional[int] = None):
        self.semester_id = semester_id
        self.term_id = term_id
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
        self.rooms: List[RoomInput] = []
        self.sessions: List[SessionInput] = []
        self.slots: List[TimeSlot] = []
        self.lecturers: Dict[int, Lecturer] = {}
        self.groups: Dict[int, StudentGroup] = {}
        
        self.x = {}

    def load_data(self):
        logger.info("Loading data for semester %s...", self.semester_id)
        
        # 1. Load Rooms
        for room in Room.objects.filter(is_active=True):
            self.rooms.append(RoomInput(
                id=room.id,
                code=room.code,
                capacity=room.capacity,
                room_type=getattr(room, 'room_type', 'lecture')
            ))

        # 2. Load Time Slots (Exclude Lunch)
        self.slots = list(TimeSlot.objects.filter(is_lunch=False).order_by('order'))

        # 3. Load Lecturers
        for lec in Lecturer.objects.all():
            self.lecturers[lec.id] = lec

        # 4. Load Student Groups
        semester = Semester.objects.get(id=self.semester_id)
        for group in StudentGroup.objects.filter(semester=semester):
            self.groups[group.id] = group

        # 5. Load Courses and Allocations (Sessions)
        courses_q = Course.objects.filter(semester=semester)
        if self.term_id:
            courses_q = courses_q.filter(term_id=self.term_id)
        else:
            courses_q = courses_q.filter(term__isnull=True)

        allocations = CourseAllocation.objects.filter(
            course__in=courses_q, 
            academic_year=semester.academic_year
        ).select_related('course', 'lecturer', 'course__programme')

        for alloc in allocations:
            course = alloc.course
            # Find the student group for this course
            group = StudentGroup.objects.filter(
                programme=course.programme, 
                semester=semester
            ).first()
            
            if not group:
                continue

            self.sessions.append(SessionInput(
                id=alloc.id,
                course_id=course.id,
                group_id=group.id,
                lecturer_id=alloc.lecturer_id,
                hours_per_week=course.hours_per_week,
                requires_lab=course.requires_lab,
                programme_level=getattr(course.programme, 'level', 'UNDERGRAD'),
                semester_number=getattr(group, 'semester_number', 1)
            ))

    def build_model(self):
        logger.info("Building OR-Tools model...")
        
        # Create Boolean Variables
        for i, session in enumerate(self.sessions):
            for room in self.rooms:
                if room.capacity < self.groups[session.group_id].head_count:
                    continue
                if session.requires_lab and room.room_type != 'lab':
                    continue

                for day in range(6): # 0=Mon to 5=Sat
                    # MASTERS/POSTGRAD CONSTRAINT: Only Saturdays
                    if session.programme_level.upper() in ['MASTERS', 'POSTGRAD']:
                        if day != DayOfWeek.SATURDAY:
                            continue
                    
                    for slot in self.slots:
                        var_name = f"x_{i}_{room.id}_{day}_{slot.id}"
                        self.x[(i, room.id, day, slot.id)] = self.model.NewBoolVar(var_name)

        # --- HARD CONSTRAINTS ---
        # 1. Each session must be scheduled exactly (hours_per_week / 2) times
        for i, session in enumerate(self.sessions):
            required_slots = max(1, session.hours_per_week // 2)
            vars_for_session = [self.x[(i, r.id, d, s.id)] for (idx, r_id, d, s_id) in self.x if idx == i]
            if vars_for_session:
                self.model.Add(sum(vars_for_session) == required_slots)

        # 2. No Room Clashes
        for room in self.rooms:
            for day in range(6):
                for slot in self.slots:
                    vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x if r_id == room.id and d == day and s_id == slot.id]
                    if vars_list:
                        self.model.Add(sum(vars_list) <= 1)

        # 3. No Lecturer Clashes
        for lec_id in self.lecturers.keys():
            for day in range(6):
                for slot in self.slots:
                    vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                                 if self.sessions[idx].lecturer_id == lec_id and d == day and s_id == slot.id]
                    if vars_list:
                        self.model.Add(sum(vars_list) <= 1)

        # 4. No Group Clashes
        for grp_id in self.groups.keys():
            for day in range(6):
                for slot in self.slots:
                    vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                                 if self.sessions[idx].group_id == grp_id and d == day and s_id == slot.id]
                    if vars_list:
                        self.model.Add(sum(vars_list) <= 1)

        # 5. Lecturer Weekly Load
        for lec_id, lecturer in self.lecturers.items():
            max_slots = getattr(lecturer, 'max_weekly_slots', 22)
            vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                         if self.sessions[idx].lecturer_id == lec_id]
            if vars_list:
                self.model.Add(sum(vars_list) <= max_slots)

        # 6. Lecturer Daily Load
        for lec_id, lecturer in self.lecturers.items():
            max_daily = getattr(lecturer, 'max_daily_slots', 6)
            for day in range(6):
                vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                             if self.sessions[idx].lecturer_id == lec_id and d == day]
                if vars_list:
                    self.model.Add(sum(vars_list) <= max_daily)

        # 7. Student Days Per Week
        for grp_id, group in self.groups.items():
            max_days = getattr(group, 'max_days_per_week', 4)
            day_used = {day: self.model.NewBoolVar(f'day_used_{grp_id}_{day}') for day in range(6)}
            
            for day in range(6):
                vars_list = [self.x[(idx, r_id, d, s_id)] for (idx, r_id, d, s_id) in self.x 
                             if self.sessions[idx].group_id == grp_id and d == day]
                if vars_list:
                    self.model.AddMaxEquality(day_used[day], vars_list)
                    
            self.model.Add(sum(day_used.values()) <= max_days)

    def solve(self, timeout_seconds: int = 120) -> bool:
        logger.info("Starting solver...")
        self.solver.parameters.max_time_in_seconds = timeout_seconds
        status = self.solver.Solve(self.model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.info("Solver found a solution!")
            return True
        else:
            logger.error("Solver failed to find a feasible solution. Status: %s", status)
            return False

    def save_results(self, timetable: Timetable):
        logger.info("Saving results to database...")
        TimetableEntry.objects.filter(timetable=timetable).delete()
        
        entries_to_create = []
        for (idx, room_id, day, slot_id), var in self.x.items():
            if self.solver.Value(var) == 1:
                session = self.sessions[idx]
                entries_to_create.append(TimetableEntry(
                    timetable=timetable,
                    course_id=session.course_id,
                    student_group_id=session.group_id,
                    lecturer_id=session.lecturer_id,
                    room_id=room_id,
                    day=day,
                    time_slot_id=slot_id
                ))
        
        TimetableEntry.objects.bulk_create(entries_to_create)