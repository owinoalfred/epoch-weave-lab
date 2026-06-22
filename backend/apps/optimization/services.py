import logging
from apps.scheduling.models import Timetable, TimetableStatus
from .engine import TimetableSolver

logger = logging.getLogger(__name__)

def generate_timetable_for_semester(semester_id: int, term_id: int = None):
    logger.info(f"Starting timetable generation for semester {semester_id}")
    
    # Create a new Timetable record
    timetable = Timetable.objects.create(
        name=f"Generated Timetable - Sem {semester_id}",
        semester_id=semester_id,
        term_id=term_id,
        status=TimetableStatus.GENERATING
    )
    
    solver = TimetableSolver(semester_id=semester_id, term_id=term_id)
    
    logger.info("Loading data into solver...")
    solver.load_data()
    
    logger.info("Building CP-SAT model...")
    solver.build_model()
    
    logger.info("Solving model...")
    success = solver.solve(timeout_seconds=300)
    
    if success:
        logger.info("Saving results to database...")
        solver.save_results(timetable)
        timetable.status = TimetableStatus.PUBLISHED
        timetable.save()
        logger.info(f"Successfully generated timetable {timetable.id}")
        return timetable
    else:
        timetable.status = TimetableStatus.DRAFT
        timetable.save()
        logger.error("Failed to generate timetable. No feasible solution found.")
        return None