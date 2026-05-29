from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.complaint import Complaint
from app.schemas.schemas import AnalyticsSummary, TrendDataPoint, RootCauseInsight
from app.services.analytics import generate_weekly_summary
from app.services.rca_generator import generate_rca
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
    # Pass days/limit down if we want, but for deep RCA we use limit=50.
    result = await generate_rca(db, limit=50)
    if not result:
        return RootCauseInsight(
            summary="No complaints found to analyze.",
            top_categories=[],
            top_products=[],
            recommendations=[]
        )
    return RootCauseInsight(**result)


@router.get("/weekly-summary")
async def get_weekly_summary(db: AsyncSession = Depends(get_db)):
    summary = await generate_weekly_summary(db)
    return {"summary": summary}


@router.get("/complaint-clusters")
async def get_complaint_clusters(db: AsyncSession = Depends(get_db)):
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sqlalchemy.orm import selectinload
    from app.models.complaint import ComplaintEmbedding

    result = await db.execute(
        select(Complaint)
        .join(ComplaintEmbedding, Complaint.id == ComplaintEmbedding.complaint_id)
        .options(selectinload(Complaint.embedding))
    )
    complaints = result.scalars().all()

    if len(complaints) < 3:
        # Return fallback empty list
        return []

    # Extract embedding vectors
    embeddings = []
    for c in complaints:
        embeddings.append(c.embedding.embedding)

    # Convert to numpy array
    X = np.array(embeddings)  # shape (N, 768)

    # Perform PCA (2 components)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    # Normalize coordinates to 0-100 range for nice UI rendering
    x_min, x_max = X_pca[:, 0].min(), X_pca[:, 0].max()
    y_min, y_max = X_pca[:, 1].min(), X_pca[:, 1].max()

    # Avoid divide by zero
    x_range = (x_max - x_min) if (x_max - x_min) > 0 else 1.0
    y_range = (y_max - y_min) if (y_max - y_min) > 0 else 1.0

    X_scaled = np.zeros_like(X_pca)
    X_scaled[:, 0] = ((X_pca[:, 0] - x_min) / x_range) * 100
    X_scaled[:, 1] = ((X_pca[:, 1] - y_min) / y_range) * 100

    # Cluster using KMeans
    n_clusters = min(5, len(complaints))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)

    # Define cluster labels based on categories or common themes
    cluster_themes = {}
    for i in range(n_clusters):
        # Find complaints in this cluster
        indices = np.where(cluster_labels == i)[0]
        cluster_complaints = [complaints[idx] for idx in indices]
        
        # Count categories in this cluster
        cats = {}
        for cc in cluster_complaints:
            cats[cc.category or "general"] = cats.get(cc.category or "general", 0) + 1
        
        # Sort and get dominant category
        sorted_cats = sorted(cats.items(), key=lambda item: item[1], reverse=True)
        dominant_cat = sorted_cats[0][0] if sorted_cats else "General Support"
        
        theme_names = {
            "billing": "Billing & Invoicing Issues",
            "refund": "Refund & Reimbursement Requests",
            "product_defect": "Product & Software Bugs",
            "account_access": "Login & Account Security",
            "service_delay": "Service Delays & Slow Support",
            "delivery": "Shipping & Delivery Queries",
            "general": "General Inquiry Cluster",
        }
        cluster_themes[i] = theme_names.get(dominant_cat, f"{dominant_cat.capitalize()} Inquiries")

    # Construct response
    points = []
    for idx, c in enumerate(complaints):
        cluster_id = int(cluster_labels[idx])
        points.append({
            "id": str(c.id),
            "subject": c.subject or "Untitled Complaint",
            "category": c.category or "general",
            "status": c.status,
            "severity": c.severity,
            "x": float(X_scaled[idx, 0]),
            "y": float(X_scaled[idx, 1]),
            "cluster_id": cluster_id,
            "cluster_label": cluster_themes[cluster_id]
        })

    return points

