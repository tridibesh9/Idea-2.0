import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"))
    escalated_by: Mapped[str] = mapped_column(String(50))  # system, agent_name
    reason: Mapped[str] = mapped_column(Text)
    previous_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    new_agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.id"))
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, acknowledged, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
