from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.mail_provider import MailProvider
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus
from app.schemas.email_classification import (
    EmailClassificationRequest,
    EmailThreadContext,
)
from app.services.classification_service import ClassificationService

def make_request(
    subject: str,
    body: str,
    thread_context: EmailThreadContext | None = None,
) -> EmailClassificationRequest:
    return EmailClassificationRequest(
        provider=MailProvider.MANUAL_TEST,
        sender_name="Test Sender",
        sender_email="test@example.com",
        subject=subject,
        body=body,
        thread_context=thread_context,
    )
    
def test_classifies_interview_request_as_high_priority_surfaceable_email():
    payload = make_request(
        subject="Interview invitation for Backend Engineer role",
        body="Hi, we would like to schedule a call with you next week.",
    )
    result = ClassificationService().classify_preview(payload)

    assert result.primary_category == EmailCategory.JOB_INTERVIEW
    assert result.thread_status == ThreadStatus.INTERVIEW_SCHEDULING
    assert result.review_status == ReviewStatus.AUTO_CLASSIFIED
    assert result.priority == EmailPriority.HIGH
    assert result.action_needed is True
    assert result.should_surface is True
    assert result.confidence >= 0.8
    
def test_classifies_interview_confirmation():
    payload = make_request(
        subject="Interview confirmed",
        body="Your interview is confirmed for tomorrow.",
    )
    result = ClassificationService().classify_preview(payload)

    assert result.primary_category == EmailCategory.INTERVIEW_CONFIRMATION
    assert result.thread_status == ThreadStatus.INTERVIEW_CONFIRMED
    assert result.priority == EmailPriority.HIGH
    assert result.action_needed is False
    assert result.should_surface is True
    
def test_classifies_rejection_with_application_update_secondary_category():
    service = ClassificationService()

    payload = make_request(
        subject="Application update",
        body="Unfortunately, we are not moving forward with your application at this time.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.REJECTION
    assert result.secondary_categories == [EmailCategory.APPLICATION_UPDATE]
    assert result.thread_status == ThreadStatus.REJECTED
    assert result.priority == EmailPriority.MEDIUM
    assert result.action_needed is False
    assert result.should_surface is True


def test_classifies_recruiter_follow_up_after_user_replied():
    service = ClassificationService()

    thread_context = EmailThreadContext(
        provider_thread_id="thread_123",
        user_has_replied=True,
        previous_thread_status=ThreadStatus.WAITING_FOR_RECRUITER_REPLY,
        last_known_company_name="Acme",
        last_known_role_title="Backend Engineer",
    )

    payload = make_request(
        subject="Re: Backend Engineer role update",
        body="Thanks for getting back to me. We have an application update and would like to discuss the next step.",
        thread_context=thread_context,
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.RECRUITER_FOLLOW_UP
    assert result.secondary_categories == [EmailCategory.APPLICATION_UPDATE]
    assert result.thread_status == ThreadStatus.WAITING_FOR_USER_REPLY
    assert result.priority == EmailPriority.HIGH
    assert result.action_needed is True
    assert result.should_surface is True
    assert result.company_name == "Acme"
    assert result.role_title == "Backend Engineer"


def test_first_recruiter_outreach_is_low_priority_and_not_surfaceable():
    service = ClassificationService()

    payload = make_request(
        subject="New backend engineer opportunity",
        body="Hi, I am a recruiter and wanted to reach out about an opportunity.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.INITIAL_RECRUITER_OUTREACH
    assert result.thread_status == ThreadStatus.NEW_OUTREACH
    assert result.priority == EmailPriority.LOW
    assert result.action_needed is False
    assert result.should_surface is False


def test_unknown_email_goes_to_unrecognized_and_needs_review():
    service = ClassificationService()

    payload = make_request(
        subject="Quick update",
        body="Thanks for your message. I will get back to you soon.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.UNRECOGNIZED
    assert result.thread_status == ThreadStatus.NEEDS_REVIEW
    assert result.review_status == ReviewStatus.NEEDS_REVIEW
    assert result.priority == EmailPriority.MEDIUM
    assert result.action_needed is True
    assert result.should_surface is True


def test_primary_category_is_not_duplicated_in_secondary_categories():
    service = ClassificationService()

    thread_context = EmailThreadContext(
        user_has_replied=True,
    )

    payload = make_request(
        subject="Interview scheduling",
        body="Thanks for your reply. We would like to schedule a call for the interview.",
        thread_context=thread_context,
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.JOB_INTERVIEW
    assert EmailCategory.JOB_INTERVIEW not in result.secondary_categories