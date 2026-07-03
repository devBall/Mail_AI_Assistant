from fastapi import APIRouter
from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus
from app.schemas.email_classification import EmailClassificationRequest, EmailClassificationResponse, EmailClassificationResult

router = APIRouter()

@router.post("/classification/preview", response_model=EmailClassificationResponse)
def preview_email_classification(payload: EmailClassificationRequest) -> EmailClassificationResponse:
    """
    Preview the email classification result based on the provided email content.
    """
    subject = payload.subject.lower()
    body = payload.body.lower()
    combined_text = f"{subject} {body}"
    
    thread_context = payload.thread_context
    user_has_replied = thread_context.user_has_replied if thread_context else False
    
    if "interview" in combined_text or "schedule a call" in combined_text:
        result = EmailClassificationResult(
            category=EmailCategory.JOB_INTERVIEW,
            thread_status=ThreadStatus.INTERVIEW_SCHEDULING,
            review_status=ReviewStatus.AUTO_CLASSIFIED,
            priority=EmailPriority.HIGH,
            confidence=0.88,
            action_needed=True,
            should_surface=True,
            company_name=thread_context.last_known_company_name if thread_context else None,
            role_title=thread_context.last_known_role_title if thread_context else None,
            reason="Fake classifier matched interview or scheduling-related wording.",
        )
        
    elif "confirmed" in combined_text and "interview" in combined_text:
        result = EmailClassificationResult(
            primary_category=EmailCategory.INTERVIEW_CONFIRMATION,
            thread_status=ThreadStatus.INTERVIEW_CONFIRMED,
            review_status=ReviewStatus.AUTO_CLASSIFIED,
            priority=EmailPriority.HIGH,
            confidence=0.88,
            action_needed=False,
            should_surface=True,
            company_name=thread_context.last_known_company_name if thread_context else None,
            role_title=thread_context.last_known_role_title if thread_context else None,
            reason="Fake classifier matched interview confirmation wording.",
        )

    elif "unfortunately" in combined_text or "not moving forward" in combined_text:
        result = EmailClassificationResult(
            primary_category=EmailCategory.REJECTION,
            thread_status=ThreadStatus.REJECTED,
            review_status=ReviewStatus.AUTO_CLASSIFIED,
            priority=EmailPriority.MEDIUM,
            confidence=0.9,
            action_needed=False,
            should_surface=True,
            company_name=thread_context.last_known_company_name if thread_context else None,
            role_title=thread_context.last_known_role_title if thread_context else None,
            reason="Fake classifier matched rejection-related wording.",
        )

    elif "assessment" in combined_text or "coding challenge" in combined_text:
        result = EmailClassificationResult(
            primary_category=EmailCategory.ASSESSMENT,
            thread_status=ThreadStatus.ASSESSMENT_STAGE,
            review_status=ReviewStatus.AUTO_CLASSIFIED,
            priority=EmailPriority.HIGH,
            confidence=0.86,
            action_needed=True,
            should_surface=True,
            company_name=thread_context.last_known_company_name if thread_context else None,
            role_title=thread_context.last_known_role_title if thread_context else None,
            reason="Fake classifier matched assessment-related wording.",
        )

    elif user_has_replied:
        result = EmailClassificationResult(
            primary_category=EmailCategory.RECRUITER_FOLLOW_UP,
            thread_status=ThreadStatus.WAITING_FOR_USER_REPLY,
            review_status=ReviewStatus.AUTO_CLASSIFIED,
            priority=EmailPriority.HIGH,
            confidence=0.78,
            action_needed=True,
            should_surface=True,
            company_name=thread_context.last_known_company_name if thread_context else None,
            role_title=thread_context.last_known_role_title if thread_context else None,
            reason="Fake classifier treated this as important because the user previously replied in this thread.",
        )

    elif "recruiter" in combined_text or "opportunity" in combined_text:
        result = EmailClassificationResult(
            primary_category=EmailCategory.INITIAL_RECRUITER_OUTREACH,
            thread_status=ThreadStatus.NEW_OUTREACH,
            review_status=ReviewStatus.AUTO_CLASSIFIED,
            priority=EmailPriority.LOW,
            confidence=0.72,
            action_needed=False,
            should_surface=False,
            reason="Fake classifier matched initial recruiter outreach wording, but it is low priority.",
        )

    else:
        result = EmailClassificationResult(
            primary_category=EmailCategory.UNRECOGNIZED_INTENT,
            thread_status=ThreadStatus.NEEDS_REVIEW,
            review_status=ReviewStatus.NEEDS_REVIEW,
            priority=EmailPriority.MEDIUM,
            confidence=0.4,
            action_needed=True,
            should_surface=True,
            reason="Fake classifier could not confidently detect the email intent.",
        )
        
    return EmailClassificationResponse(input=payload, classification=result)