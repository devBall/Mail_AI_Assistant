from app.enums.email_category import EmailCategory
from app.enums.email_priority import EmailPriority
from app.enums.review_status import ReviewStatus
from app.enums.thread_status import ThreadStatus
from app.schemas.email_classification import (
    EmailClassificationRequest,
    EmailClassificationResult,
)


class ClassificationService:
    def classify_preview(
        self,
        payload: EmailClassificationRequest,
    ) -> EmailClassificationResult:
        subject = payload.subject.lower()
        body = payload.body.lower()
        combined_text = f"{subject} {body}"

        thread_context = payload.thread_context
        user_has_replied = thread_context.user_has_replied if thread_context else False

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

        if "confirmed" in combined_text and "interview" in combined_text:
            return EmailClassificationResult(
                primary_category=EmailCategory.INTERVIEW_CONFIRMATION,
                secondary_categories=[],
                thread_status=ThreadStatus.INTERVIEW_CONFIRMED,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.HIGH,
                confidence=0.88,
                action_needed=False,
                should_surface=True,
                company_name=company_name,
                role_title=role_title,
                reason="Fake classifier matched interview confirmation wording.",
            )

        if "interview" in combined_text or "schedule a call" in combined_text:
            secondary_categories: list[EmailCategory] = []

            if user_has_replied:
                secondary_categories.append(EmailCategory.RECRUITER_FOLLOW_UP)

            return EmailClassificationResult(
                primary_category=EmailCategory.JOB_INTERVIEW,
                secondary_categories=secondary_categories,
                thread_status=ThreadStatus.INTERVIEW_SCHEDULING,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.HIGH,
                confidence=0.88,
                action_needed=True,
                should_surface=True,
                company_name=company_name,
                role_title=role_title,
                reason="Fake classifier matched interview or scheduling-related wording.",
            )

        if "unfortunately" in combined_text or "not moving forward" in combined_text:
            secondary_categories: list[EmailCategory] = []

            if "application" in combined_text:
                secondary_categories.append(EmailCategory.APPLICATION_UPDATE)

            return EmailClassificationResult(
                primary_category=EmailCategory.REJECTION,
                secondary_categories=secondary_categories,
                thread_status=ThreadStatus.REJECTED,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.MEDIUM,
                confidence=0.9,
                action_needed=False,
                should_surface=True,
                company_name=company_name,
                role_title=role_title,
                reason="Fake classifier matched rejection-related wording.",
            )

        if "assessment" in combined_text or "coding challenge" in combined_text:
            secondary_categories: list[EmailCategory] = []

            if user_has_replied:
                secondary_categories.append(EmailCategory.RECRUITER_FOLLOW_UP)

            return EmailClassificationResult(
                primary_category=EmailCategory.ASSESSMENT,
                secondary_categories=secondary_categories,
                thread_status=ThreadStatus.ASSESSMENT_STAGE,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.HIGH,
                confidence=0.86,
                action_needed=True,
                should_surface=True,
                company_name=company_name,
                role_title=role_title,
                reason="Fake classifier matched assessment-related wording.",
            )

        if user_has_replied:
            secondary_categories: list[EmailCategory] = []

            if "update" in combined_text or "next step" in combined_text:
                secondary_categories.append(EmailCategory.APPLICATION_UPDATE)

            return EmailClassificationResult(
                primary_category=EmailCategory.RECRUITER_FOLLOW_UP,
                secondary_categories=secondary_categories,
                thread_status=ThreadStatus.WAITING_FOR_USER_REPLY,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.HIGH,
                confidence=0.78,
                action_needed=True,
                should_surface=True,
                company_name=company_name,
                role_title=role_title,
                reason="Fake classifier treated this as important because the user previously replied in this thread.",
            )

        if "recruiter" in combined_text or "opportunity" in combined_text:
            return EmailClassificationResult(
                primary_category=EmailCategory.INITIAL_RECRUITER_OUTREACH,
                secondary_categories=[],
                thread_status=ThreadStatus.NEW_OUTREACH,
                review_status=ReviewStatus.AUTO_CLASSIFIED,
                priority=EmailPriority.LOW,
                confidence=0.72,
                action_needed=False,
                should_surface=False,
                company_name=company_name,
                role_title=role_title,
                reason="Fake classifier matched initial recruiter outreach wording, but it is low priority.",
            )

        return EmailClassificationResult(
            primary_category=EmailCategory.UNRECOGNIZED,
            secondary_categories=[],
            thread_status=ThreadStatus.NEEDS_REVIEW,
            review_status=ReviewStatus.NEEDS_REVIEW,
            priority=EmailPriority.MEDIUM,
            confidence=0.4,
            action_needed=True,
            should_surface=True,
            company_name=company_name,
            role_title=role_title,
            reason="Fake classifier could not confidently detect the email intent.",
        )


classification_service = ClassificationService()