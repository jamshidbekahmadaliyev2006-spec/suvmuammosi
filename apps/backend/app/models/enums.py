from enum import StrEnum


class Role(StrEnum):
    USER = "USER"


class SourceType(StrEnum):
    CHANNEL = "CHANNEL"
    GROUP = "GROUP"
    BOT = "BOT"



class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"
    INVALID = "INVALID"
    DUPLICATE = "DUPLICATE"


class IncidentCategory(StrEnum):
    PIPE_BURST = "PIPE_BURST"
    SUPPLY_OUTAGE = "SUPPLY_OUTAGE"
    LOW_PRESSURE = "LOW_PRESSURE"
    LEAK = "LEAK"
    FLOODING = "FLOODING"
    PLANNED_REPAIR = "PLANNED_REPAIR"
    SEWAGE = "SEWAGE"
    OTHER = "OTHER"
    UNCLEAR = "UNCLEAR"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MatchType(StrEnum):
    CONTAINS = "CONTAINS"
    WHOLE_WORD = "WHOLE_WORD"
    PHRASE = "PHRASE"


class ProcessingStatus(StrEnum):
    RECEIVED = "RECEIVED"
    NO_MATCH = "NO_MATCH"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    LINKED = "LINKED"
    # Inkor / hal bo'lgan / noaniq xabarlar: hodisa yaratilmaydi, foydalanuvchi ko'radi.
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
