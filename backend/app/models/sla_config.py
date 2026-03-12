import uuid
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SLAConfig(Base):
    __tablename__ = "sla_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    severity: Mapped[str] = mapped_column(String(20), unique=True)  # critical, high, medium, low
    max_resolution_hours: Mapped[int] = mapped_column(Integer)  # 4, 8, 24, 72
    escalation_threshold_pct: Mapped[int] = mapped_column(Integer, default=80)  # escalate at 80% of deadline
