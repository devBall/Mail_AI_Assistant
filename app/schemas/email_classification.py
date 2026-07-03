from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.enums.email_priority import EmailPriority
from app.enums.review_status import ReviewStatus
from app.enums.mail_provider import MailProvider
from app.enums.email_category import EmailCategory
from app.enums.thread_status import ThreadStatus

class EmailThreadContext(BaseModel):
    provider_thread_id: Optional[str] = None

    user_has_replied: bool = False
    previous_thread_status: Optional[ThreadStatus] = None

    last_known_company_name: Optional[str] = None
    last_known_role_title: Optional[str] = None

    last_email_category: Optional[EmailCategory] = None
    last_email_received_at: Optional[datetime] = None

class EmailClassificationRequest(BaseModel):
    """Request model for email classification."""
    provider: MailProvider = MailProvider.MANUAL_TEST
    provider_message_id: Optional[str] = None
    provider_thread_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: str
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")
    received_at: Optional[datetime] = None
    thread_context: Optional[EmailThreadContext] = None
    
class EmailClassificationResult(BaseModel):
    """Result model for email classification."""
    primary_category: EmailCategory
    secondary_categories: list[EmailCategory] = Field(default_factory=list, max_length=2)
    thread_status: ThreadStatus
    review_status: ReviewStatus
    priority: EmailPriority
    
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the classification.")
    
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    
    action_needed: bool = False
    should_surface: bool = False
    
    interview_date: Optional[datetime] = None
    reason:str = Field(..., min_length=1, max_length=1000)
    
    @feld_validator('secondary_categories')
    def validate_secondary_categories(cls, values:list[EmailCategory]) -> list[EmailCategory]:
        unique_values = list(set(values))
        for value in values:
            if value not in unique_values:
                unique_values.append(value)
                
        return unique_values

class EmailClassificationResponse(BaseModel):
    """Response model for email classification."""
    input: EmailClassificationRequest
    classification: EmailClassificationResult