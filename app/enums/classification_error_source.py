from enum import StrEnum


class ClassificationErrorSource(StrEnum):
    ANTHROPIC = "ANTHROPIC"

    MICROSOFT_GRAPH = "MICROSOFT_GRAPH"
    GMAIL = "GMAIL"

    INTERNAL = "INTERNAL"
    UNKNOWN = "UNKNOWN"