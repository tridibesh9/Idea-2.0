import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.escalation import Escalation
from app.schemas.schemas import EscalationResponse
from app.services.handover_report import generate_handover_report

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

@router.get("/handover/{complaint_id}")
async def get_handover_report(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    report = await generate_handover_report(complaint_id, db)
    if not report:
        return {"report": "Complaint not found or report could not be generated."}
    return {"report": report}
