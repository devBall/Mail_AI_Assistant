from __future__ import annotations

from datetime import datetime
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
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.enums.thread_status import ThreadStatus

if TYPE_CHECKING:
    from app.models.email import Email
    from app.models.mail_account import MailAccount


class EmailThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_threads"

    __table_args__ = (
        UniqueConstraint(
            "mail_account_id",
            "provider_thread_id",
            name="uq_email_threads_account_provider_thread",
        ),
        CheckConstraint(
            "message_count >= 0",
            name="message_count_nonnegative",
        ),
        Index(
            "ix_email_threads_account_latest_message",
            "mail_account_id",
            "latest_message_at",
        ),
        Index(
            "ix_email_threads_account_status",
            "mail_account_id",
            "current_thread_status",
        ),
    )

    mail_account_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "mail_accounts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider_thread_id: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )

    normalized_subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    current_thread_status: Mapped[ThreadStatus] = mapped_column(
        Enum(
            ThreadStatus,
            name="thread_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=ThreadStatus.UNCLASSIFIED,
        server_default=ThreadStatus.UNCLASSIFIED.value,
    )

    user_has_replied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    latest_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latest_inbound_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latest_outbound_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    mail_account: Mapped[MailAccount] = relationship(
        back_populates="email_threads",
    )

    emails: Mapped[list[Email]] = relationship(
        back_populates="email_thread",
        passive_deletes=True,
    )