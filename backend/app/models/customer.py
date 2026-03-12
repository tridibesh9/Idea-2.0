import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(300), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    account_id: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    complaints: Mapped[list["Complaint"]] = relationship(back_populates="customer")
