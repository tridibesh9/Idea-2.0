import uuid
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.escalation import Escalation
from app.models.complaint import Complaint
from app.models.agent import Agent
from app.models.audit_log import AuditLog
from app.schemas.schemas import EscalationResponse
from app.services.handover_report import generate_handover_report
from app.services.auth import get_current_agent

router = APIRouter()

class EscalationCreate(BaseModel):
    complaint_id: uuid.UUID
    reason: str
    target_agent_id: Optional[uuid.UUID] = None

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

@router.post("", response_model=EscalationResponse, status_code=201)
async def create_escalation(
    payload: EscalationCreate,
    db: AsyncSession = Depends(get_db),
    current_agent: Optional[dict] = Depends(get_current_agent)
):
    # Verify complaint exists
    complaint_res = await db.execute(select(Complaint).where(Complaint.id == payload.complaint_id))
    complaint = complaint_res.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    prev_agent_id = complaint.assigned_agent_id
    new_agent_id = payload.target_agent_id

    if not new_agent_id:
        # Default to first supervisor/manager in Management
        supervisor_res = await db.execute(
            select(Agent).where(Agent.role.in_(["supervisor", "senior_official"]))
        )
        supervisor = supervisor_res.scalars().first()
        if supervisor:
            new_agent_id = supervisor.id

    complaint.assigned_agent_id = new_agent_id
    complaint.status = "escalated"

    escalated_by_name = current_agent.get("email") if current_agent else "agent"

    escalation = Escalation(
        complaint_id=payload.complaint_id,
        escalated_by=escalated_by_name,
        reason=payload.reason,
        previous_agent_id=prev_agent_id,
        new_agent_id=new_agent_id,
        status="active"
    )
    db.add(escalation)

    audit = AuditLog(
        complaint_id=payload.complaint_id,
        action="complaint_escalated",
        performed_by=escalated_by_name,
        details=json.dumps({"reason": payload.reason})
    )
    db.add(audit)
    await db.flush()

    return escalation

@router.get("/handover/{complaint_id}")
async def get_handover_report(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    report = await generate_handover_report(complaint_id, db)
    if not report:
        return {"report": "Complaint not found or report could not be generated."}
    return {"report": report}
