import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from app.database import Base
from app.services.security import get_encryption_key


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(100), index=True)
    channel: Mapped[str] = mapped_column(String(50), index=True)  # email, chat, twitter, phone, web_form
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(StringEncryptedType(Text, get_encryption_key, FernetEngine))

    # Relationships
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))

    # AI Classification
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    product: Mapped[str | None] = mapped_column(String(200))
    severity: Mapped[str] = mapped_column(String(20), default="medium", index=True)  # critical, high, medium, low
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    sentiment_label: Mapped[str | None] = mapped_column(String(20))  # positive, neutral, negative
    key_issues: Mapped[str | None] = mapped_column(Text)  # JSON array stored as text
    ai_confidence_score: Mapped[float | None] = mapped_column(Float)
    regulatory_flags: Mapped[str | None] = mapped_column(Text)  # JSON array stored as text
    next_best_action: Mapped[str | None] = mapped_column(Text)
    incident_group_id: Mapped[str | None] = mapped_column(String(100), index=True)

    # Status & SLA
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)  # new, open, in_progress, escalated, resolved, closed
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    messages: Mapped[list["ComplaintMessage"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")
    embedding: Mapped["ComplaintEmbedding | None"] = relationship(back_populates="complaint", cascade="all, delete-orphan", uselist=False)
    customer: Mapped["Customer | None"] = relationship(back_populates="complaints", foreign_keys=[customer_id])
    agent: Mapped["Agent | None"] = relationship(back_populates="assigned_complaints", foreign_keys=[assigned_agent_id])
    entities: Mapped[list["Entity"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")


class ComplaintMessage(Base):
    __tablename__ = "complaint_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"))
    sender_type: Mapped[str] = mapped_column(String(20))  # customer, agent, system
    sender_name: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    channel: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    complaint: Mapped["Complaint"] = relationship(back_populates="messages")


class ComplaintEmbedding(Base):
    __tablename__ = "complaint_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"), unique=True)
    embedding = mapped_column(Vector(768))  # Gemini text-embedding-004 dimension

    complaint: Mapped["Complaint"] = relationship(back_populates="embedding")
