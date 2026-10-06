from src.schemas.tools import DraftSupportTicketRequest, DraftSupportTicketResponse
from src.core.tools import draft_support_ticket

class HumanInTheLoopError(Exception):
    """Raised when a user explicitly rejects an action during a HITL check."""
    pass


def confirm_ticket_draft_cli_ui(request: DraftSupportTicketRequest) -> DraftSupportTicketResponse:
    """
    Human-in-the-Loop (HITL) UI for ticket confirmation.
    In a CLI environment, this prompts the user for approval before finalizing the ticket.
    In a web API environment, this logic would instead pause the orchestrator and return 
    a 'requires_action' state to the frontend.
    """
    print("\n" + "="*50)
    print("⚠️  HUMAN-IN-THE-LOOP CONFIRMATION REQUIRED ⚠️")
    print("="*50)
    print(f"The agent is proposing to draft a support ticket.")
    print(f"Student ID: {request.student_id}")
    print(f"Category:   {request.issue_category}")
    print(f"Issue:\n{request.issue_description}")
    print("-" * 50)
    
    while True:
        choice = input("Do you approve this ticket submission? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            print("Ticket approved. Proceeding with execution...")
            # User approved, so we actually call the underlying tool
            return draft_support_ticket(request)
        elif choice in ['n', 'no']:
            print("Ticket rejected by user.")
            raise HumanInTheLoopError("The user reviewed the draft ticket and rejected its submission.")
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def demonstrate_hitl():
    """A small test function to demonstrate the UI flow."""
    request = DraftSupportTicketRequest(
        student_id="123456",
        issue_category="IT Support",
        issue_description="I cannot log into the student portal. It keeps saying 'Invalid Credentials' even though I reset my password."
    )
    
    try:
        response = confirm_ticket_draft_cli_ui(request)
        print("\n✅ Final Result:")
        print(response.model_dump_json(indent=2))
    except HumanInTheLoopError as e:
        print(f"\n❌ Execution Halted: {e}")

if __name__ == "__main__":
    # If this file is run directly, demonstrate the UI.
    demonstrate_hitl()
