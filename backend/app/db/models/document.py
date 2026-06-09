import uuid
from datetime import datetime

from app.db.models.enums import DocumentStatus, enum_values
from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, DateTime, Enum, ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
  __tablename__ = "documents"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
    nullable=False,
  )

  file_name: Mapped[str] = mapped_column(Text, nullable=False)
  file_url: Mapped[str] = mapped_column(Text, nullable=False)
  mime_type: Mapped[str | None] = mapped_column(Text)

  status: Mapped[DocumentStatus] = mapped_column(
    Enum(
      DocumentStatus,
      name="document_status",
      values_callable=enum_values,
      create_constraint=True,
    ),
    server_default=text("'pending'"),
  )

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
  chunks: Mapped[list["DocumentChunk"]] = relationship(
    back_populates="document", cascade="all, delete-orphan"
  )


class DocumentChunk(Base):
  __tablename__ = "document_chunks"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
  )
  document_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
  )

  chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
  content: Mapped[str] = mapped_column(Text, nullable=False)
  embedding: Mapped[list[float] | None] = mapped_column(Vector(3072))

  # 'metadata' is mapped to 'metadata_' to avoid conflicts with SQLAlchemy's internal MetaData object
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

  created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
  )

  # Relationships
  document: Mapped["Document"] = relationship(back_populates="chunks")
