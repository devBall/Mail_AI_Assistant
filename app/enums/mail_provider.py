from enum import StrEnum

class MailProvider(StrEnum):
    """Enum for mail providers."""
    GMAIL = "GMAIL"
    OUTLOOK = "OUTLOOK"
    OTHER = "OTHER"
    MANUAL_TEST = "MANUAL_TEST"