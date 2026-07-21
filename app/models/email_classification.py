from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.enums.classification_error_source import ClassificationErrorSource
from app.enums.classification_origin import ClassificationOrigin
from app.enums.classification_status import ClassificationStatus
from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus

if TYPE_CHECKING:
    from app.models.classification_attempt import ClassificationAttempt
    from app.models.email import Email


class EmailClassification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "email_classifications"

    __table_args__ = (
        UniqueConstraint(
            "email_id",
            name="uq_email_classifications_email",
        ),
        UniqueConstraint(
            "source_attempt_id",
            name="uq_email_classifications_source_attempt",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="confidence_range",
        ),
        CheckConstraint(
            "classification_version > 0",
            name="classification_version_positive",
        ),
        Index(
            "ix_email_classifications_category_received",
            "primary_category",
            "classified_at",
        ),
        Index(
            "ix_email_classifications_review_status",
            "review_status",
            "classified_at",
        ),
        Index(
            "ix_email_classifications_processing_status",
            "classification_status",
            "classified_at",
        ),
        Index(
            "ix_email_classifications_surface_priority",
            "should_surface",
            "priority",
        ),
    )

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "emails.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    source_attempt_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "classification_attempts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    primary_category: Mapped[EmailCategory] = mapped_column(
        Enum(
            EmailCategory,
            name="email_category",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    secondary_categories: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    thread_status: Mapped[ThreadStatus] = mapped_column(
        Enum(
            ThreadStatus,
            name="thread_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(
            ReviewStatus,
            name="review_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    priority: Mapped[EmailPriority] = mapped_column(
        Enum(
            EmailPriority,
            name="email_priority",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    classification_status: Mapped[ClassificationStatus] = mapped_column(
        Enum(
            ClassificationStatus,
            name="classification_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    origin: Mapped[ClassificationOrigin] = mapped_column(
        Enum(
            ClassificationOrigin,
            name="classification_origin",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    company_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    role_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    action_needed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    should_surface: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    interview_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prompt_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="v1",
        server_default="v1",
    )

    classification_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    error_source: Mapped[ClassificationErrorSource | None] = mapped_column(
        Enum(
            ClassificationErrorSource,
            name="classification_error_source",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    email: Mapped[Email] = relationship(
        back_populates="classification",
    )

    source_attempt: Mapped[ClassificationAttempt | None] = relationship(
        foreign_keys=[source_attempt_id],
    )