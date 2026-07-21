from enum import StrEnum


class ClassificationOrigin(StrEnum):
    ANTHROPIC = "ANTHROPIC"
    FALLBACK_RULES = "FALLBACK_RULES"
    USER_REVIEW = "USER_REVIEW"