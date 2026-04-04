import enum


class ReportType(str, enum.Enum):
    ROBBERY = "robbery"
    ASSAULT_VIOLENCE = "assault/violence"
    HARASSMENT = "harassment"
    ROADBLOCKS = "road_blocks"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    RESOLVED = "resolved"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    REPORTER = "reporter"


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AuditAction(str, enum.Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    SEVERITY_CHANGED = "severity_changed"
    ASSIGNED = "assigned"
    APPROVED = "approved"
    DESCRIPTION_EDITED = "description_edited"
    MEDIA_ADDED = "media_added"
    MEDIA_REMOVED = "media_removed"


class ActorType(str, enum.Enum):
    USER = "user"
    ANONYMOUS = "anonymous"
    SYSTEM = "system"
