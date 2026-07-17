from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING
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
from app.enums.classification_trigger import ClassificationTrigger
from app.enums.email_category import EmailCategory

if TYPE_CHECKING:
    from app.models.email import Email


class ClassificationAttempt(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "classification_attempts"

    __table_args__ = (
        UniqueConstraint(
            "origin",
            "provider_request_id",
            name="uq_classification_attempts_origin_request_id",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="latency_ms_nonnegative",
        ),
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name="input_tokens_nonnegative",
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name="output_tokens_nonnegative",
        ),
        CheckConstraint(
            "estimated_cost_usd IS NULL OR estimated_cost_usd >= 0",
            name="estimated_cost_nonnegative",
        ),
        CheckConstraint(
            """
            predicted_confidence IS NULL
            OR (
                predicted_confidence >= 0
                AND predicted_confidence <= 1
            )
            """,
            name="predicted_confidence_range",
        ),
        Index(
            "ix_classification_attempts_email_created_at",
            "email_id",
            "created_at",
        ),
        Index(
            "ix_classification_attempts_status_created_at",
            "status",
            "created_at",
        ),
        Index(
            "ix_classification_attempts_origin_created_at",
            "origin",
            "created_at",
        ),
        Index(
            "ix_classification_attempts_input_fingerprint",
            "input_fingerprint",
        ),
    )

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "emails.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    retry_of_attempt_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "classification_attempts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
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

    trigger: Mapped[ClassificationTrigger] = mapped_column(
        Enum(
            ClassificationTrigger,
            name="classification_trigger",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=ClassificationTrigger.EMAIL_INGESTION,
        server_default=ClassificationTrigger.EMAIL_INGESTION.value,
    )

    status: Mapped[ClassificationStatus] = mapped_column(
        Enum(
            ClassificationStatus,
            name="classification_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=ClassificationStatus.PENDING,
        server_default=ClassificationStatus.PENDING.value,
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

    provider_request_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    input_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    request_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    response_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    raw_response_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    predicted_primary_category: Mapped[EmailCategory | None] = mapped_column(
        Enum(
            EmailCategory,
            name="email_category",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=True,
    )

    predicted_secondary_categories: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    predicted_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    was_applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    estimated_cost_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 8),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        back_populates="classification_attempts",
    )