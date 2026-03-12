import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.escalation import Escalation
from app.schemas.schemas import EscalationResponse

router = APIRouter()


@router.get("", response_model=list[EscalationResponse])
async def list_escalations(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Escalation).order_by(Escalation.created_at.desc())
    if status:
        query = query.where(Escalation.status == status)
    result = await db.execute(query)
    return result.scalars().all()
