from dataclasses import dataclass
from typing import Literal

import pytest

from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.mail_provider import MailProvider
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus
from app.schemas.email_classification import (
    EmailClassificationRequest,
    EmailThreadContext,
)

from app.services import classification_service as classification_service_module
from app.services.classification_service import ClassificationService

@dataclass
class FakeSettings:
    ai_classifier_mode: Literal["fallback", "anthropic"] = "fallback"
    
@pytest.fixture(autouse=True)
def force_fallback_mode(monkeypatch):
    monkeypatch.setattr(
        classification_service_module,
        "get_settings",
        lambda: FakeSettings(ai_classifier_mode="fallback"),
    )
        

def make_request(
    subject: str,
    body: str,
    thread_context: EmailThreadContext | None = None,
) -> EmailClassificationRequest:
    return EmailClassificationRequest(
        provider=MailProvider.MANUAL_TEST,
        sender_name="Jane Recruiter",
        sender_email="jane@company.com",
        subject=subject,
        body=body,
        thread_context=thread_context,
    )


def test_fallback_classifies_not_moving_forward_as_rejection():
    service = ClassificationService()

    payload = make_request(
        subject="Application update",
        body="Unfortunately, we are not moving forward with your application at this time.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.REJECTION
    assert result.secondary_categories == [EmailCategory.APPLICATION_UPDATE]
    assert result.thread_status == ThreadStatus.REJECTED
    assert result.review_status == ReviewStatus.AUTO_CLASSIFIED
    assert result.priority == EmailPriority.MEDIUM
    assert result.action_needed is False
    assert result.should_surface is True
    assert result.confidence >= 0.8


def test_fallback_classifies_pursue_other_candidates_as_rejection():
    service = ClassificationService()

    payload = make_request(
        subject="Update regarding your candidacy",
        body="After careful consideration, we have decided to pursue other candidates.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.REJECTION
    assert result.thread_status == ThreadStatus.REJECTED
    assert result.review_status == ReviewStatus.AUTO_CLASSIFIED
    assert result.should_surface is True


def test_fallback_sends_interview_email_to_manual_review():
    service = ClassificationService()

    payload = make_request(
        subject="Interview invitation",
        body="We would like to schedule a call with you next week.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.UNRECOGNIZED
    assert result.thread_status == ThreadStatus.NEEDS_REVIEW
    assert result.review_status == ReviewStatus.NEEDS_REVIEW
    assert result.priority == EmailPriority.MEDIUM
    assert result.action_needed is True
    assert result.should_surface is True


def test_fallback_sends_recruiter_follow_up_to_manual_review():
    service = ClassificationService()

    thread_context = EmailThreadContext(
        provider_thread_id="thread_123",
        user_has_replied=True,
        previous_thread_status=ThreadStatus.WAITING_FOR_RECRUITER_REPLY,
        last_known_company_name="Acme",
        last_known_role_title="Backend Engineer",
    )

    payload = make_request(
        subject="Re: Backend Engineer role",
        body="Thanks for getting back to me. Are you available tomorrow?",
        thread_context=thread_context,
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.UNRECOGNIZED
    assert result.thread_status == ThreadStatus.NEEDS_REVIEW
    assert result.review_status == ReviewStatus.NEEDS_REVIEW
    assert result.company_name == "Acme"
    assert result.role_title == "Backend Engineer"
    assert result.should_surface is True


def test_fallback_sends_initial_recruiter_outreach_to_manual_review():
    service = ClassificationService()

    payload = make_request(
        subject="New backend engineer opportunity",
        body="Hi, I am a recruiter and wanted to reach out about an opportunity.",
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.UNRECOGNIZED
    assert result.thread_status == ThreadStatus.NEEDS_REVIEW
    assert result.review_status == ReviewStatus.NEEDS_REVIEW
    assert result.should_surface is True


def test_fallback_preserves_thread_context_company_and_role():
    service = ClassificationService()

    thread_context = EmailThreadContext(
        last_known_company_name="Acme",
        last_known_role_title="Backend Engineer",
    )

    payload = make_request(
        subject="Quick update",
        body="Thanks for your message. I will get back to you soon.",
        thread_context=thread_context,
    )

    result = service.classify_preview(payload)

    assert result.primary_category == EmailCategory.UNRECOGNIZED
    assert result.company_name == "Acme"
    assert result.role_title == "Backend Engineer"