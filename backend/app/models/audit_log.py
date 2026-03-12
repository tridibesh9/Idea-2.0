import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"))
    action: Mapped[str] = mapped_column(String(100))  # created, classified, assigned, escalated, responded, resolved, closed
    performed_by: Mapped[str] = mapped_column(String(200))  # agent name or "system"
    details: Mapped[str | None] = mapped_column(Text)  # JSON with extra context
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
