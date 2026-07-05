from app.core.config import get_settings
from app.enums.classification_error_source import ClassificationErrorSource
from app.enums.classification_status import ClassificationStatus
from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus
from app.integrations.anthropic_client import (
    AnthropicClassificationClient,
    AnthropicClassificationError,
)
from app.schemas.email_classification import (
    EmailClassificationRequest,
    EmailClassificationResult,
)


class ClassificationService:
    def classify_preview(
        self,
        payload: EmailClassificationRequest,
    ) -> EmailClassificationResult:
        settings = get_settings()

        if settings.AI_CLASSIFIER_MODE == "anthropic":
            return self.classify_with_anthropic(payload)

        return self.classify_with_fallback_rules(payload)

    def classify_with_anthropic(
        self,
        payload: EmailClassificationRequest,
    ) -> EmailClassificationResult:
        try:
            client = AnthropicClassificationClient()
            return client.classify_email(payload)

        except AnthropicClassificationError as exc:
            return self.build_api_error_result(
                payload=payload,
                error_source=ClassificationErrorSource.ANTHROPIC,
                error_message=str(exc),
            )

        except Exception as exc:
            return self.build_api_error_result(
                payload=payload,
                error_source=ClassificationErrorSource.UNKNOWN,
                error_message=str(exc),
            )

    def classify_with_fallback_rules(
        self,
        payload: EmailClassificationRequest,
    ) -> EmailClassificationResult:
        subject = payload.subject.lower()
        body = payload.body.lower()
        combined_text = f"{subject} {body}"

        thread_context = payload.thread_context

        company_name = (
            thread_context.last_known_company_name
            if thread_context
            else None
        )
        role_title = (
            thread_context.last_known_role_title
            if thread_context
            else None
        )

        if self._looks_like_rejection(combined_text):
            secondary_categories: list[EmailCategory] = []

            if "application" in combined_text:
                secondary_categories.append(EmailCategory.APPLICATION_UPDATE)

            return EmailClassificationResult(
                primary_category=EmailCategory.REJECTION,
                secondary_categories=secondary_categories,
                thread_status=ThreadStatus.REJECTED,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.MEDIUM,
                classification_status=ClassificationStatus.COMPLETED,
                confidence=0.82,
                action_needed=False,
                should_surface=True,
                company_name=company_name,
                role_title=role_title,
                reason="Fallback rule matched a strong rejection phrase.",
            )

        return EmailClassificationResult(
            primary_category=EmailCategory.UNRECOGNIZED,
            secondary_categories=[],
            thread_status=ThreadStatus.NEEDS_REVIEW,
            review_status=ReviewStatus.NEEDS_REVIEW,
            priority=EmailPriority.MEDIUM,
            classification_status=ClassificationStatus.NEEDS_REVIEW,
            confidence=0.3,
            action_needed=True,
            should_surface=True,
            company_name=company_name,
            role_title=role_title,
            reason="Fallback rules could not safely classify this email, so it requires manual review.",
        )

    def build_api_error_result(
        self,
        payload: EmailClassificationRequest,
        error_source: ClassificationErrorSource,
        error_message: str,
    ) -> EmailClassificationResult:
        thread_context = payload.thread_context

        company_name = (
            thread_context.last_known_company_name
            if thread_context
            else None
        )
        role_title = (
            thread_context.last_known_role_title
            if thread_context
            else None
        )

        return EmailClassificationResult(
            primary_category=EmailCategory.UNRECOGNIZED,
            secondary_categories=[],
            thread_status=ThreadStatus.NEEDS_REVIEW,
            review_status=ReviewStatus.NEEDS_REVIEW,
            priority=EmailPriority.HIGH,
            classification_status=ClassificationStatus.FAILED,
            confidence=0.0,
            action_needed=True,
            should_surface=True,
            company_name=company_name,
            role_title=role_title,
            error_source=error_source,
            error_message=error_message[:1000],
            reason="Classification failed because the AI provider returned an error.",
        )

    def _looks_like_rejection(self, text: str) -> bool:
        rejection_phrases = [
            "not moving forward",
            "not move forward",
            "unable to move forward",
            "will not be moving forward",
            "will not be proceeding",
            "decided not to proceed",
            "not selected",
            "not chosen",
            "pursue other candidates",
            "pursuing other candidates",
            "unfortunately",
            "we regret to inform",
            "after careful consideration",
        ]

        return any(phrase in text for phrase in rejection_phrases)


classification_service = ClassificationService()