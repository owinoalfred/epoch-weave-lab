from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import generate_timetable_for_semester

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def trigger_solver(request):
    """
    Triggers the OR-Tools solver to generate a timetable for a specific semester.
    Expected POST data: {"semester_id": 1, "term_id": 1} (term_id is optional)
    """
    semester_id = request.data.get("semester_id")
    term_id = request.data.get("term_id")
    
    if not semester_id:
        return Response({"error": "semester_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        timetable = generate_timetable_for_semester(semester_id, term_id)
        if timetable:
            return Response({
                "success": True, 
                "timetable_id": timetable.id, 
                "message": "Timetable generated successfully!"
            })
        else:
            return Response({
                "success": False, 
                "message": "Solver could not find a feasible solution. Try relaxing constraints or adding more rooms/slots."
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)