from enum import Enum as PyEnum


def enum_values(enum_cls: type[PyEnum]) -> list[str]:
  return [member.value for member in enum_cls]


class KnowledgeScope(PyEnum):
  WORKSPACE = "workspace"
  CAMPAIGN = "campaign"


class DocumentStatus(PyEnum):
  PENDING = "pending"
  PROCESSING = "processing"
  INDEXED = "indexed"
  FAILED = "failed"


class CampaignStatus(PyEnum):
  DRAFT = "draft"
  RESEARCHING = "researching"
  GENERATING = "generating"
  APPROVAL_PENDING = "approval_pending"
  COMPLETED = "completed"
  FAILED = "failed"


class ContentPlatform(PyEnum):
  TWITTER = "twitter"
  LINKEDIN = "linkedin"
  EMAIL = "email"
  BLOG = "blog"


class ContentStatus(PyEnum):
  DRAFT = "draft"
  APPROVED = "approved"
  REJECTED = "rejected"
  PUBLISHED = "published"
  FAILED = "failed"


class AgentStatus(PyEnum):
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"


class LogLevel(PyEnum):
  INFO = "info"
  WARNING = "warning"
  ERROR = "error"
