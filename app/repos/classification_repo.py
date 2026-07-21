from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classification_attempt import ClassificationAttempt
from app.models.email_classification import EmailClassification


class ClassificationRepository:
    def create_attempt(
        self,
        db: Session,
        attempt: ClassificationAttempt,
    ) -> ClassificationAttempt:
        db.add(attempt)
        db.flush()

        return attempt

    def get_current_for_update(
        self,
        db: Session,
        email_id: UUID,
    ) -> EmailClassification | None:
        statement = (
            select(EmailClassification)
            .where(EmailClassification.email_id == email_id)
            .with_for_update()
        )

        return db.scalar(statement)

    def create_current(
        self,
        db: Session,
        classification: EmailClassification,
    ) -> EmailClassification:
        db.add(classification)
        db.flush()

        return classification


classification_repository = ClassificationRepository()