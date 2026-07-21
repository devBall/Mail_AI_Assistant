from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums.classification_origin import ClassificationOrigin
from app.enums.classification_trigger import ClassificationTrigger
from app.schemas.email_classification import EmailClassificationResult


class ClassificationPersistenceCommand(BaseModel):
    email_id: UUID

    result: EmailClassificationResult

    origin: ClassificationOrigin
    trigger: ClassificationTrigger = ClassificationTrigger.EMAIL_INGESTION

    model_name: str | None = None
    prompt_version: str = "v1"

    provider_request_id: str | None = None
    input_fingerprint: str | None = None

    request_metadata: dict[str, Any] | None = None
    raw_response_text: str | None = None

    latency_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)

    estimated_cost_usd: Decimal | None = Field(
        default=None,
        ge=0,
    )

    retry_of_attempt_id: UUID | None = None


class ClassificationPersistenceResult(BaseModel):
    attempt_id: UUID
    classification_id: UUID | None
    applied: bool
    classification_version: int | None