import uuid
from typing import Dict, Any
from src.schemas.tools import (
    GetStudentStatusRequest,
    GetStudentStatusResponse,
    DraftSupportTicketRequest,
    DraftSupportTicketResponse
)

# Mock database for deterministic student status tool
MOCK_STUDENT_DB = {
    "123456": {
        "status": "Enrolled",
        "enrolled_program": "Bachelor of Science in Software Engineering",
        "financial_hold": False,
        "message": "Student is in good standing."
    },
    "987654": {
        "status": "Suspended",
        "enrolled_program": "Bachelor of Information Technology",
        "financial_hold": True,
        "message": "Student has pending tuition fees from the previous semester."
    },
    "111222": {
        "status": "Graduated",
        "enrolled_program": "Bachelor of Computer Science",
        "financial_hold": False,
        "message": "Graduated in 2025."
    }
}


def get_student_status(request: GetStudentStatusRequest) -> GetStudentStatusResponse:
    """
    Deterministic Tool: Retrieves the status of a student based on their ID.
    """
    student_id = request.student_id
    
    if student_id in MOCK_STUDENT_DB:
        data = MOCK_STUDENT_DB[student_id]
        return GetStudentStatusResponse(
            student_id=student_id,
            status=data["status"],
            enrolled_program=data.get("enrolled_program"),
            financial_hold=data.get("financial_hold", False),
            message=data.get("message")
        )
    else:
        # Default response for unknown students
        return GetStudentStatusResponse(
            student_id=student_id,
            status="Unknown",
            enrolled_program=None,
            financial_hold=False,
            message="Student ID not found in the system."
        )


def draft_support_ticket(request: DraftSupportTicketRequest) -> DraftSupportTicketResponse:
    """
    Triage Tool: Drafts a new support ticket for a student issue.
    """
    # Generate a deterministic-looking ticket ID for triage
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    # In a real system, this would save to a database.
    # Here, we just acknowledge the draft creation.
    return DraftSupportTicketResponse(
        ticket_id=ticket_id,
        status="Drafted",
        message=f"Successfully drafted a {request.issue_category} ticket for student {request.student_id}. Pending human-in-the-loop confirmation."
    )
