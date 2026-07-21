from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import EmailNotFoundError
from app.enums.classification_error_source import ClassificationErrorSource
from app.enums.classification_origin import ClassificationOrigin
from app.enums.classification_status import ClassificationStatus
from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus
from app.models.classification_attempt import ClassificationAttempt
from app.models.email_classification import EmailClassification
from app.schemas.classification_persistence import (
    ClassificationPersistenceCommand,
)
from app.schemas.email_classification import EmailClassificationResult
from app.services.classification_persistence_service import (
    ClassificationPersistenceService,
)


class FakeSession:
    def flush(self) -> None:
        pass


class FakeEmailRepository:
    def __init__(self, email=None) -> None:
        self.email = email

    def get_by_id(
        self,
        db: FakeSession,
        email_id: UUID,
    ):
        if self.email is None:
            return None

        if self.email.id != email_id:
            return None

        return self.email


class FakeClassificationRepository:
    def __init__(
        self,
        current: EmailClassification | None = None,
    ) -> None:
        self.current = current
        self.attempts: list[ClassificationAttempt] = []

    def create_attempt(
        self,
        db: FakeSession,
        attempt: ClassificationAttempt,
    ) -> ClassificationAttempt:
        if attempt.id is None:
            attempt.id = uuid4()

        self.attempts.append(attempt)
        return attempt

    def get_current_for_update(
        self,
        db: FakeSession,
        email_id: UUID,
    ) -> EmailClassification | None:
        if self.current is None:
            return None

        if self.current.email_id != email_id:
            return None

        return self.current

    def create_current(
        self,
        db: FakeSession,
        classification: EmailClassification,
    ) -> EmailClassification:
        if classification.id is None:
            classification.id = uuid4()

        self.current = classification
        return classification


def make_success_result(
    category: EmailCategory = EmailCategory.JOB_INTERVIEW,
) -> EmailClassificationResult:
    return EmailClassificationResult(
        primary_category=category,
        secondary_categories=[],
        thread_status=ThreadStatus.INTERVIEW_SCHEDULING,
        review_status=ReviewStatus.AUTO_CLASSIFIED,
        priority=EmailPriority.HIGH,
        classification_status=ClassificationStatus.COMPLETED,
        confidence=0.94,
        company_name="Acme",
        role_title="Backend Engineer",
        action_needed=True,
        should_surface=True,
        reason="The email asks the candidate to schedule an interview.",
    )


def make_failed_result() -> EmailClassificationResult:
    return EmailClassificationResult(
        primary_category=EmailCategory.UNRECOGNIZED,
        secondary_categories=[],
        thread_status=ThreadStatus.NEEDS_REVIEW,
        review_status=ReviewStatus.NEEDS_REVIEW,
        priority=EmailPriority.HIGH,
        classification_status=ClassificationStatus.FAILED,
        confidence=0.0,
        action_needed=True,
        should_surface=True,
        reason="Classification failed because the AI provider returned an error.",
        error_source=ClassificationErrorSource.ANTHROPIC,
        error_message="Anthropic request failed: timeout",
    )


def make_command(
    email_id: UUID,
    result: EmailClassificationResult,
) -> ClassificationPersistenceCommand:
    return ClassificationPersistenceCommand(
        email_id=email_id,
        result=result,
        origin=ClassificationOrigin.ANTHROPIC,
        model_name="claude-haiku-4-5-20251001",
        prompt_version="v1",
        provider_request_id=f"request-{uuid4()}",
        latency_ms=500,
        input_tokens=400,
        output_tokens=100,
        estimated_cost_usd=Decimal("0.001"),
    )


def make_existing_classification(
    email_id: UUID,
    category: EmailCategory = EmailCategory.JOB_INTERVIEW,
    status: ClassificationStatus = ClassificationStatus.COMPLETED,
    version: int = 1,
) -> EmailClassification:
    return EmailClassification(
        id=uuid4(),
        email_id=email_id,
        source_attempt_id=None,
        primary_category=category,
        secondary_categories=[],
        thread_status=ThreadStatus.INTERVIEW_SCHEDULING,
        review_status=ReviewStatus.AUTO_CLASSIFIED,
        priority=EmailPriority.HIGH,
        classification_status=status,
        origin=ClassificationOrigin.ANTHROPIC,
        confidence=Decimal("0.9400"),
        company_name="Acme",
        role_title="Backend Engineer",
        action_needed=True,
        should_surface=True,
        reason="Existing valid classification.",
        model_name="claude-haiku-4-5-20251001",
        prompt_version="v1",
        classification_version=version,
        error_source=None,
        error_message=None,
    )
    
    
def test_raises_error_when_email_does_not_exist():
    email_id = uuid4()

    email_repo = FakeEmailRepository(email=None)
    classification_repo = FakeClassificationRepository()

    service = ClassificationPersistenceService(
        email_repo=email_repo,
        classification_repo=classification_repo,
    )

    command = make_command(
        email_id=email_id,
        result=make_success_result(),
    )

    with pytest.raises(EmailNotFoundError):
        service.persist(
            db=FakeSession(),
            command=command,
        )

    assert classification_repo.attempts == []
    assert classification_repo.current is None


def test_first_successful_result_creates_attempt_and_current_classification():
    email_id = uuid4()
    email = SimpleNamespace(id=email_id)

    email_repo = FakeEmailRepository(email=email)
    classification_repo = FakeClassificationRepository()

    service = ClassificationPersistenceService(
        email_repo=email_repo,
        classification_repo=classification_repo,
    )

    persistence_result = service.persist(
        db=FakeSession(),
        command=make_command(
            email_id=email_id,
            result=make_success_result(),
        ),
    )

    assert persistence_result.applied is True
    assert persistence_result.classification_version == 1

    assert len(classification_repo.attempts) == 1

    attempt = classification_repo.attempts[0]

    assert attempt.status == ClassificationStatus.COMPLETED
    assert attempt.was_applied is True
    assert attempt.predicted_primary_category == EmailCategory.JOB_INTERVIEW

    current = classification_repo.current

    assert current is not None
    assert current.primary_category == EmailCategory.JOB_INTERVIEW
    assert current.classification_status == ClassificationStatus.COMPLETED
    assert current.classification_version == 1
    assert current.source_attempt_id == attempt.id


def test_failed_retry_does_not_replace_valid_current_classification():
    email_id = uuid4()
    email = SimpleNamespace(id=email_id)

    existing = make_existing_classification(
        email_id=email_id,
        category=EmailCategory.JOB_INTERVIEW,
        status=ClassificationStatus.COMPLETED,
        version=2,
    )

    original_classification_id = existing.id
    original_source_attempt_id = existing.source_attempt_id

    email_repo = FakeEmailRepository(email=email)
    classification_repo = FakeClassificationRepository(
        current=existing,
    )

    service = ClassificationPersistenceService(
        email_repo=email_repo,
        classification_repo=classification_repo,
    )

    persistence_result = service.persist(
        db=FakeSession(),
        command=make_command(
            email_id=email_id,
            result=make_failed_result(),
        ),
    )

    assert persistence_result.applied is False
    assert persistence_result.classification_id == original_classification_id
    assert persistence_result.classification_version == 2

    assert len(classification_repo.attempts) == 1

    failed_attempt = classification_repo.attempts[0]

    assert failed_attempt.status == ClassificationStatus.FAILED
    assert failed_attempt.was_applied is False
    assert failed_attempt.error_source == ClassificationErrorSource.ANTHROPIC

    current = classification_repo.current

    assert current.primary_category == EmailCategory.JOB_INTERVIEW
    assert current.classification_status == ClassificationStatus.COMPLETED
    assert current.classification_version == 2
    assert current.source_attempt_id == original_source_attempt_id


def test_first_failed_result_creates_failed_current_classification():
    email_id = uuid4()
    email = SimpleNamespace(id=email_id)

    email_repo = FakeEmailRepository(email=email)
    classification_repo = FakeClassificationRepository()

    service = ClassificationPersistenceService(
        email_repo=email_repo,
        classification_repo=classification_repo,
    )

    persistence_result = service.persist(
        db=FakeSession(),
        command=make_command(
            email_id=email_id,
            result=make_failed_result(),
        ),
    )

    assert persistence_result.applied is True
    assert persistence_result.classification_version == 1

    assert len(classification_repo.attempts) == 1

    attempt = classification_repo.attempts[0]
    current = classification_repo.current

    assert attempt.was_applied is True
    assert attempt.status == ClassificationStatus.FAILED

    assert current is not None
    assert current.primary_category == EmailCategory.UNRECOGNIZED
    assert current.classification_status == ClassificationStatus.FAILED
    assert current.error_source == ClassificationErrorSource.ANTHROPIC
    assert current.classification_version == 1


def test_successful_reclassification_updates_current_and_increments_version():
    email_id = uuid4()
    email = SimpleNamespace(id=email_id)

    existing = make_existing_classification(
        email_id=email_id,
        category=EmailCategory.JOB_INTERVIEW,
        status=ClassificationStatus.COMPLETED,
        version=1,
    )

    email_repo = FakeEmailRepository(email=email)
    classification_repo = FakeClassificationRepository(
        current=existing,
    )

    service = ClassificationPersistenceService(
        email_repo=email_repo,
        classification_repo=classification_repo,
    )

    rejection_result = EmailClassificationResult(
        primary_category=EmailCategory.REJECTION,
        secondary_categories=[EmailCategory.APPLICATION_UPDATE],
        thread_status=ThreadStatus.REJECTED,
        review_status=ReviewStatus.AUTO_CLASSIFIED,
        priority=EmailPriority.MEDIUM,
        classification_status=ClassificationStatus.COMPLETED,
        confidence=0.91,
        company_name="Acme",
        role_title="Backend Engineer",
        action_needed=False,
        should_surface=True,
        reason="The company is not moving forward with the application.",
    )

    persistence_result = service.persist(
        db=FakeSession(),
        command=make_command(
            email_id=email_id,
            result=rejection_result,
        ),
    )

    assert persistence_result.applied is True
    assert persistence_result.classification_version == 2

    current = classification_repo.current
    attempt = classification_repo.attempts[0]

    assert current.primary_category == EmailCategory.REJECTION
    assert current.secondary_categories == [
        EmailCategory.APPLICATION_UPDATE.value
    ]
    assert current.thread_status == ThreadStatus.REJECTED
    assert current.classification_version == 2
    assert current.source_attempt_id == attempt.id
    assert attempt.was_applied is True