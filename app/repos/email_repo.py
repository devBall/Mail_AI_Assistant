from uuid import UUID

from sqlalchemy.orm import Session

from app.models.email import Email


class EmailRepository:
    def get_by_id(
        self,
        db: Session,
        email_id: UUID,
    ) -> Email | None:
        return db.get(Email, email_id)


email_repository = EmailRepository()