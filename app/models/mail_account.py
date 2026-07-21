from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.enums.mail_account_status import MailAccountStatus
from app.enums.mailbox_provider import MailboxProvider

if TYPE_CHECKING:
    from app.models.email import Email
    from app.models.email_thread import EmailThread
    from app.models.user import User


class MailAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mail_accounts"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            "provider_subject",
            name="uq_mail_accounts_user_provider_subject",
        ),
        Index(
            "ix_mail_accounts_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_mail_accounts_provider_email",
            "provider",
            "email_address",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    provider: Mapped[MailboxProvider] = mapped_column(
        Enum(
            MailboxProvider,
            name="mailbox_provider",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    provider_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    provider_tenant_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email_address: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[MailAccountStatus] = mapped_column(
        Enum(
            MailAccountStatus,
            name="mail_account_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=MailAccountStatus.ACTIVE,
        server_default=MailAccountStatus.ACTIVE.value,
    )

    last_connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    disconnected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="mail_accounts",
    )

    email_threads: Mapped[list[EmailThread]] = relationship(
        back_populates="mail_account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    emails: Mapped[list[Email]] = relationship(
        back_populates="mail_account",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )