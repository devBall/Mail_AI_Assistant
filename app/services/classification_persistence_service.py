from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import EmailNotFoundError
from app.enums.classification_status import ClassificationStatus
from app.models.classification_attempt import ClassificationAttempt
from app.models.email_classification import EmailClassification
from app.repos.classification_repo import (
    ClassificationRepository,
    classification_repository,
)
from app.repos.email_repo import (
    EmailRepository,
    email_repository,
)
from app.schemas.classification_persistence import (
    ClassificationPersistenceCommand,
    ClassificationPersistenceResult,
)


class ClassificationPersistenceService:
    def __init__(
        self,
        email_repo: EmailRepository,
        classification_repo: ClassificationRepository,
    ) -> None:
        self.email_repo = email_repo
        self.classification_repo = classification_repo

    def persist(
        self,
        db: Session,
        command: ClassificationPersistenceCommand,
    ) -> ClassificationPersistenceResult:
        email = self.email_repo.get_by_id(
            db=db,
            email_id=command.email_id,
        )

        if email is None:
            raise EmailNotFoundError(command.email_id)

        now = datetime.now(timezone.utc)
        result = command.result

        attempt = ClassificationAttempt(
            email_id=command.email_id,
            retry_of_attempt_id=command.retry_of_attempt_id,
            origin=command.origin,
            trigger=command.trigger,
            status=result.classification_status,
            model_name=command.model_name,
            prompt_version=command.prompt_version,
            provider_request_id=command.provider_request_id,
            input_fingerprint=command.input_fingerprint,
            request_metadata=command.request_metadata,
            response_payload=result.model_dump(mode="json"),
            raw_response_text=command.raw_response_text,
            predicted_primary_category=result.primary_category,
            predicted_secondary_categories=[
                category.value
                for category in result.secondary_categories
            ],
            predicted_confidence=Decimal(str(result.confidence)),
            latency_ms=command.latency_ms,
            input_tokens=command.input_tokens,
            output_tokens=command.output_tokens,
            estimated_cost_usd=command.estimated_cost_usd,
            completed_at=now,
            error_source=result.error_source,
            error_message=result.error_message,
            was_applied=False,
        )

        self.classification_repo.create_attempt(
            db=db,
            attempt=attempt,
        )

        current = self.classification_repo.get_current_for_update(
            db=db,
            email_id=command.email_id,
        )

        should_apply = self._should_apply_result(
            current=current,
            new_status=result.classification_status,
        )

        if not should_apply:
            return ClassificationPersistenceResult(
                attempt_id=attempt.id,
                classification_id=current.id if current else None,
                applied=False,
                classification_version=(
                    current.classification_version
                    if current
                    else None
                ),
            )

        if current is None:
            current = EmailClassification(
                email_id=command.email_id,
                source_attempt_id=attempt.id,
                primary_category=result.primary_category,
                secondary_categories=[
                    category.value
                    for category in result.secondary_categories
                ],
                thread_status=result.thread_status,
                review_status=result.review_status,
                priority=result.priority,
                classification_status=result.classification_status,
                origin=command.origin,
                confidence=Decimal(str(result.confidence)),
                company_name=result.company_name,
                role_title=result.role_title,
                action_needed=result.action_needed,
                should_surface=result.should_surface,
                interview_at=result.interview_date,
                reason=result.reason,
                model_name=command.model_name,
                prompt_version=command.prompt_version,
                classification_version=1,
                classified_at=now,
                error_source=result.error_source,
                error_message=result.error_message,
            )

            self.classification_repo.create_current(
                db=db,
                classification=current,
            )
        else:
            self._update_current(
                current=current,
                command=command,
                attempt=attempt,
                classified_at=now,
            )

        attempt.was_applied = True
        db.flush()

        return ClassificationPersistenceResult(
            attempt_id=attempt.id,
            classification_id=current.id,
            applied=True,
            classification_version=current.classification_version,
        )

    def _should_apply_result(
        self,
        current: EmailClassification | None,
        new_status: ClassificationStatus,
    ) -> bool:
        if current is None:
            return True

        if new_status == ClassificationStatus.FAILED:
            return current.classification_status == ClassificationStatus.FAILED

        return True

    def _update_current(
        self,
        current: EmailClassification,
        command: ClassificationPersistenceCommand,
        attempt: ClassificationAttempt,
        classified_at: datetime,
    ) -> None:
        result = command.result

        current.source_attempt_id = attempt.id
        current.primary_category = result.primary_category
        current.secondary_categories = [
            category.value
            for category in result.secondary_categories
        ]
        current.thread_status = result.thread_status
        current.review_status = result.review_status
        current.priority = result.priority
        current.classification_status = result.classification_status
        current.origin = command.origin
        current.confidence = Decimal(str(result.confidence))

        current.company_name = result.company_name
        current.role_title = result.role_title

        current.action_needed = result.action_needed
        current.should_surface = result.should_surface

        current.interview_at = result.interview_date

        current.reason = result.reason
        current.model_name = command.model_name
        current.prompt_version = command.prompt_version

        current.error_source = result.error_source
        current.error_message = result.error_message

        current.classification_version += 1
        current.classified_at = classified_at


classification_persistence_service = ClassificationPersistenceService(
    email_repo=email_repository,
    classification_repo=classification_repository,
)