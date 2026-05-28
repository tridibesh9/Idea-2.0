import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id"))
    entity_type: Mapped[str] = mapped_column(String(100), index=True)  # e.g., CUSTOMER_ID, CREDIT_CARD
    entity_value: Mapped[str] = mapped_column(Text)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    complaint: Mapped["Complaint"] = relationship(back_populates="entities")
