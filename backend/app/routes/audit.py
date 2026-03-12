import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.schemas import AuditLogResponse

router = APIRouter()


@router.get("/{complaint_id}", response_model=list[AuditLogResponse])
async def get_audit_trail(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.complaint_id == complaint_id)
        .order_by(AuditLog.created_at)
    )
    return result.scalars().all()
