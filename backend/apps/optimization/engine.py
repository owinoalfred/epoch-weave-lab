import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
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
        
        # Indexed variable storage for efficient constraint building
        self.x = {}  # (session_idx, room_id, day, slot_id) -> BoolVar
        self.vars_by_room = {}  # (room_id, day, slot_id) -> [vars]
        self.vars_by_lecturer = {}  # (lecturer_id, day, slot_id) -> [vars]
        self.vars_by_group = {}  # (group_id, day, slot_id) -> [vars]
        self.vars_by_session = {}  # session_idx -> [vars]
        self.vars_by_lecturer_day = {}  # (lecturer_id, day) -> [vars]
        self.vars_by_group_day = {}  # (group_id, day) -> [vars]

    def load_data(self):
        logger.info("Loading data for semester %s...", self.semester_id)
        
        # 1. Load Rooms
        for room in Room.objects.filter(is_active=True):
            self.rooms.append(RoomInput(
                id=room.id,
                code=room.code,
                capacity=room.capacity,
                room_type=getattr(room, 'room_type', 'LECTURE')
            ))
        logger.info(f"Loaded {len(self.rooms)} rooms")

        # 2. Load Time Slots (Exclude Lunch)
        self.slots = list(TimeSlot.objects.filter(is_lunch=False).order_by('order'))
        logger.info(f"Loaded {len(self.slots)} time slots")

        # 3. Load Lecturers
        for lec in Lecturer.objects.filter(is_active=True):
            self.lecturers[lec.id] = lec
        logger.info(f"Loaded {len(self.lecturers)} lecturers")

        # 4. Load Student Groups
        semester = Semester.objects.get(id=self.semester_id)
        for group in StudentGroup.objects.filter(semester=semester):
            self.groups[group.id] = group
        logger.info(f"Loaded {len(self.groups)} student groups")

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

        # Get all groups for this semester
        all_groups = list(StudentGroup.objects.filter(semester=semester))
        
        for alloc in allocations:
            course = alloc.course
            
            # Find ALL student groups for this course's programme and semester
            relevant_groups = [g for g in all_groups if g.programme_id == course.programme_id]
            
            if not relevant_groups:
                logger.warning(f"No student groups found for course {course.code} in programme {course.programme_id}")
                continue

            # Create a session for EACH group that needs this course
            for group in relevant_groups:
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
        
        logger.info(f"Created {len(self.sessions)} sessions to schedule")

    def build_model(self):
        logger.info("Building OR-Tools model...")
        
        # Create Boolean Variables and build indexes
        for i, session in enumerate(self.sessions):
            group = self.groups.get(session.group_id)
            if not group:
                continue
                
            for room in self.rooms:
                # Skip rooms that are too small
                if room.capacity < group.head_count:
                    continue
                
                # Skip non-lab rooms for lab courses
                if session.requires_lab and room.room_type not in ['LAB', 'COMPUTER_LAB']:
                    continue

                for day in range(6):  # 0=Mon to 5=Sat
                    # MASTERS/POSTGRAD CONSTRAINT: Only Saturdays
                    if session.programme_level.upper() in ['MASTERS', 'POSTGRAD']:
                        if day != DayOfWeek.SATURDAY:
                            continue
                    
                    for slot in self.slots:
                        var_name = f"x_{i}_{room.id}_{day}_{slot.id}"
                        var = self.model.NewBoolVar(var_name)
                        
                        # Store in main dict
                        key = (i, room.id, day, slot.id)
                        self.x[key] = var
                        
                        # Build indexes for efficient constraint building
                        self.vars_by_session.setdefault(i, []).append(var)
                        
                        room_key = (room.id, day, slot.id)
                        self.vars_by_room.setdefault(room_key, []).append(var)
                        
                        lec_key = (session.lecturer_id, day, slot.id)
                        self.vars_by_lecturer.setdefault(lec_key, []).append(var)
                        
                        grp_key = (session.group_id, day, slot.id)
                        self.vars_by_group.setdefault(grp_key, []).append(var)
                        
                        lec_day_key = (session.lecturer_id, day)
                        self.vars_by_lecturer_day.setdefault(lec_day_key, []).append(var)
                        
                        grp_day_key = (session.group_id, day)
                        self.vars_by_group_day.setdefault(grp_day_key, []).append(var)

        logger.info(f"Created {len(self.x)} boolean variables")

        # --- HARD CONSTRAINTS ---
        
        # 1. Each session must be scheduled exactly (hours_per_week / 2) times
        for i, session in enumerate(self.sessions):
            required_slots = max(1, session.hours_per_week // 2)
            vars_for_session = self.vars_by_session.get(i, [])
            if vars_for_session:
                self.model.Add(sum(vars_for_session) == required_slots)

        # 2. No Room Clashes (max 1 session per room per time slot)
        for room_key, vars_list in self.vars_by_room.items():
            if vars_list:
                self.model.Add(sum(vars_list) <= 1)

        # 3. No Lecturer Clashes (max 1 session per lecturer per time slot)
        for lec_key, vars_list in self.vars_by_lecturer.items():
            if vars_list:
                self.model.Add(sum(vars_list) <= 1)

        # 4. No Group Clashes (max 1 session per group per time slot)
        for grp_key, vars_list in self.vars_by_group.items():
            if vars_list:
                self.model.Add(sum(vars_list) <= 1)

        # 5. Lecturer Weekly Load
        for lec_id, lecturer in self.lecturers.items():
            max_slots = getattr(lecturer, 'max_weekly_slots', 22)
            all_vars = []
            for day in range(6):
                all_vars.extend(self.vars_by_lecturer_day.get((lec_id, day), []))
            if all_vars:
                self.model.Add(sum(all_vars) <= max_slots)

        # 6. Lecturer Daily Load
        for lec_id, lecturer in self.lecturers.items():
            max_daily = getattr(lecturer, 'max_daily_slots', 6)
            for day in range(6):
                vars_list = self.vars_by_lecturer_day.get((lec_id, day), [])
                if vars_list:
                    self.model.Add(sum(vars_list) <= max_daily)

        # 7. Student Days Per Week
        for grp_id, group in self.groups.items():
            max_days = getattr(group, 'max_days_per_week', 4)
            day_used = {day: self.model.NewBoolVar(f'day_used_{grp_id}_{day}') for day in range(6)}
            
            for day in range(6):
                vars_list = self.vars_by_group_day.get((grp_id, day), [])
                if vars_list:
                    self.model.AddMaxEquality(day_used[day], vars_list)
                else:
                    # If no variables for this day, it's not used
                    self.model.Add(day_used[day] == 0)
                    
            self.model.Add(sum(day_used.values()) <= max_days)

        logger.info("Model building complete. Adding to solver...")

    def solve(self, timeout_seconds: int = 300) -> bool:
        logger.info(f"Starting solver with {timeout_seconds}s timeout...")
        self.solver.parameters.max_time_in_seconds = timeout_seconds
        
        # Enable solver logging for debugging
        self.solver.parameters.log_search_progress = True
        
        status = self.solver.Solve(self.model)
        
        if status == cp_model.OPTIMAL:
            logger.info("Solver found OPTIMAL solution!")
            return True
        elif status == cp_model.FEASIBLE:
            logger.info("Solver found FEASIBLE solution!")
            return True
        else:
            logger.error(f"Solver failed. Status: {status}")
            return False

    def save_results(self, timetable: Timetable):
        logger.info("Saving results to database...")
        
        # Delete any existing entries for this timetable
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
        
        if entries_to_create:
            TimetableEntry.objects.bulk_create(entries_to_create)
            logger.info(f"Successfully saved {len(entries_to_create)} timetable entries")
        else:
            logger.warning("No timetable entries to save - solver found no solution")