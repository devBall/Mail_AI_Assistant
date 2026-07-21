from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.enums.email_direction import EmailDirection

if TYPE_CHECKING:
    from app.models.classification_attempt import ClassificationAttempt
    from app.models.email_classification import EmailClassification
    from app.models.email_thread import EmailThread
    from app.models.mail_account import MailAccount


class Email(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "emails"

    __table_args__ = (
        UniqueConstraint(
            "mail_account_id",
            "provider_message_id",
            name="uq_emails_account_provider_message",
        ),
        UniqueConstraint(
            "mail_account_id",
            "provider_immutable_id",
            name="uq_emails_account_provider_immutable",
        ),
        Index(
            "ix_emails_account_received_at",
            "mail_account_id",
            "received_at",
        ),
        Index(
            "ix_emails_thread_received_at",
            "email_thread_id",
            "received_at",
        ),
        Index(
            "ix_emails_sender_email",
            "sender_email",
        ),
        Index(
            "ix_emails_account_deleted",
            "mail_account_id",
            "is_provider_deleted",
        ),
    )

    mail_account_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "mail_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    email_thread_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "email_threads.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    provider_message_id: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    provider_immutable_id: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    internet_message_id: Mapped[str | None] = mapped_column(
        String(998),
        nullable=True,
    )

    provider_parent_folder_id: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    provider_change_key: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    web_link: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    direction: Mapped[EmailDirection] = mapped_column(
        Enum(
            EmailDirection,
            name="email_direction",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=EmailDirection.UNKNOWN,
        server_default=EmailDirection.UNKNOWN.value,
    )

    sender_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sender_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    reply_to: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    to_recipients: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    cc_recipients: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    bcc_recipients: Mapped[list[dict[str, str]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    body_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    body_preview: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    provider_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    provider_modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    has_attachments: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_provider_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    provider_deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    mail_account: Mapped[MailAccount] = relationship(
        back_populates="emails",
    )

    email_thread: Mapped[EmailThread | None] = relationship(
        back_populates="emails",
    )

    classification: Mapped[EmailClassification | None] = relationship(
        back_populates="email",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    classification_attempts: Mapped[list[ClassificationAttempt]] = relationship(
        back_populates="email",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )