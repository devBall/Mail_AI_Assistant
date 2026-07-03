from fastapi import APIRouter
from app.schemas.email_classification import EmailClassificationRequest, EmailClassificationResponse
from app.services.classification_service import classification_service

router = APIRouter()

@router.post("/classification/preview", response_model=EmailClassificationResponse)
def preview_email_classification(payload: EmailClassificationRequest) -> EmailClassificationResponse:
    """
    Preview the email classification result based on the provided email content.
    """
    classification = classification_service.classify_preview(payload)
    
    
        
    return EmailClassificationResponse(input=payload, classification=classification)