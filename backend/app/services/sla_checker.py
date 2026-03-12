import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.complaint import Complaint
from app.models.escalation import Escalation
from app.models.audit_log import AuditLog

logger = logging.getLogger("sla_checker")


async def check_sla_breaches():
    """Background task: mark complaints that have breached their SLA deadline."""
    async with async_session() as db:
        try:
            now = datetime.now(timezone.utc)
            open_statuses = ["new", "open", "in_progress", "escalated"]

            result = await db.execute(
                select(Complaint).where(
                    Complaint.status.in_(open_statuses),
                    Complaint.is_sla_breached == False,
                    Complaint.sla_deadline.isnot(None),
                    Complaint.sla_deadline < now,
                )
            )
            breached = result.scalars().all()

            for complaint in breached:
                complaint.is_sla_breached = True
                complaint.updated_at = now

                # Create escalation
                escalation = Escalation(
                    complaint_id=complaint.id,
                    escalated_by="system",
                    reason=f"SLA breached — deadline was {complaint.sla_deadline.isoformat()}",
                    status="active",
                )
                db.add(escalation)

                # Audit log
                audit = AuditLog(
                    complaint_id=complaint.id,
                    action="sla_breached",
                    performed_by="system",
                    details=json.dumps({
                        "sla_deadline": complaint.sla_deadline.isoformat(),
                        "severity": complaint.severity,
                    }),
                )
                db.add(audit)

                # Broadcast via WebSocket if available
                try:
                    from app.routes.websocket import manager
                    await manager.broadcast({
                        "type": "sla_breach",
                        "complaint_id": str(complaint.id),
                        "subject": complaint.subject,
                        "severity": complaint.severity,
                    })
                except Exception:
                    pass

            await db.commit()

            if breached:
                logger.info(f"SLA checker: marked {len(breached)} complaints as breached")
        except Exception as e:
            await db.rollback()
            logger.error(f"SLA checker error: {e}")
