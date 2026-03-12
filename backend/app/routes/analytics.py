from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.complaint import Complaint
from app.schemas.schemas import AnalyticsSummary, TrendDataPoint, RootCauseInsight
from app.services.analytics import generate_root_cause_insight, generate_weekly_summary

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    open_statuses = ["new", "open", "in_progress", "escalated"]

    total_open = (await db.execute(
        select(func.count(Complaint.id)).where(Complaint.status.in_(open_statuses))
    )).scalar() or 0

    total_critical = (await db.execute(
        select(func.count(Complaint.id)).where(
            Complaint.severity == "critical",
            Complaint.status.in_(open_statuses),
        )
    )).scalar() or 0

    total_sla_breached = (await db.execute(
        select(func.count(Complaint.id)).where(Complaint.is_sla_breached == True)
    )).scalar() or 0

    avg_sentiment = (await db.execute(
        select(func.avg(Complaint.sentiment_score))
    )).scalar()

    # Avg resolution time for resolved complaints
    resolved = (await db.execute(
        select(Complaint).where(Complaint.status.in_(["resolved", "closed"]), Complaint.resolved_at.isnot(None))
    )).scalars().all()

    avg_hours = None
    if resolved:
        total_hours = sum(
            (c.resolved_at - c.created_at).total_seconds() / 3600 for c in resolved
        )
        avg_hours = round(total_hours / len(resolved), 1)

    return AnalyticsSummary(
        total_open=total_open,
        total_critical=total_critical,
        total_sla_breached=total_sla_breached,
        avg_resolution_hours=avg_hours,
        avg_sentiment=round(avg_sentiment, 2) if avg_sentiment else None,
    )


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_trends(
    days: int = Query(30, ge=1, le=365),
    group_by: str = Query("category", regex="^(category|channel|severity)$"),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Complaint.created_at).label("date"),
            getattr(Complaint, group_by).label("group_field"),
            func.count(Complaint.id).label("count"),
        )
        .where(Complaint.created_at >= since)
        .group_by(func.date(Complaint.created_at), getattr(Complaint, group_by))
        .order_by(func.date(Complaint.created_at))
    )
    rows = result.all()
    field_map = {"category": "category", "channel": "channel", "severity": "category"}
    return [
        TrendDataPoint(date=str(r.date), count=r.count, **{field_map.get(group_by, "category"): r.group_field})
        for r in rows
    ]


@router.get("/root-cause", response_model=RootCauseInsight)
async def get_root_cause(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    return await generate_root_cause_insight(db, days)


@router.get("/weekly-summary")
async def get_weekly_summary(db: AsyncSession = Depends(get_db)):
    summary = await generate_weekly_summary(db)
    return {"summary": summary}
