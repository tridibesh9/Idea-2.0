import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from app.database import Base
from app.services.security import get_encryption_key


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(StringEncryptedType(String(300), get_encryption_key, FernetEngine))
    email_hash: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(StringEncryptedType(String(50), get_encryption_key, FernetEngine))
    account_id: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    complaints: Mapped[list["Complaint"]] = relationship(back_populates="customer")
