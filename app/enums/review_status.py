from enum import StrEnum

class ReviewStatus(StrEnum):
    """Enum for review statuses."""
    AUTO_CLASSIFIED = "AUTO_CLASSIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    USER_CONFIRMED = "USER_CONFIRMED"
    USER_CORRECTED = "USER_CORRECTED"