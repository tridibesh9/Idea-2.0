from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.complaint import Complaint
from app.schemas.schemas import AnalyticsSummary, TrendDataPoint, RootCauseInsight
from app.services.analytics import generate_weekly_summary, generate_root_cause_insight
from app.services.analytics_cache import analytics_cache

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    cache_key = "summary"
    cached = analytics_cache.get(cache_key)
    if cached is not None:
        return cached

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

    res = AnalyticsSummary(
        total_open=total_open,
        total_critical=total_critical,
        total_sla_breached=total_sla_breached,
        avg_resolution_hours=avg_hours,
        avg_sentiment=round(avg_sentiment, 2) if avg_sentiment else None,
    )
    analytics_cache.set(cache_key, res)
    return res


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_trends(
    timeframe: str = Query("30d", regex="^(1h|12h|24h|7d|30d)$"),
    group_by: str = Query("category", regex="^(category|channel|severity)$"),
    db: AsyncSession = Depends(get_db),
):
    # Use timeframe parameter as cache key instead of days
    cache_key = f"trends_{timeframe}_{group_by}"
    cached = analytics_cache.get(cache_key)
    if cached is not None:
        return cached

    now = datetime.now(timezone.utc)
    if timeframe == "1h":
        since = now - timedelta(hours=1)
        date_expr = func.to_char(Complaint.created_at, 'YYYY-MM-DD HH24:MI')
    elif timeframe == "12h":
        since = now - timedelta(hours=12)
        date_expr = func.to_char(Complaint.created_at, 'YYYY-MM-DD HH24:00')
    elif timeframe == "24h":
        since = now - timedelta(hours=24)
        date_expr = func.to_char(Complaint.created_at, 'YYYY-MM-DD HH24:00')
    elif timeframe == "7d":
        since = now - timedelta(days=7)
        date_expr = func.date(Complaint.created_at)
    else:  # 30d
        since = now - timedelta(days=30)
        date_expr = func.date(Complaint.created_at)

    result = await db.execute(
        select(
            date_expr.label("date"),
            getattr(Complaint, group_by).label("group_field"),
            func.count(Complaint.id).label("count"),
        )
        .where(Complaint.created_at >= since)
        .group_by(date_expr, getattr(Complaint, group_by))
        .order_by(date_expr)
    )
    rows = result.all()
    field_map = {"category": "category", "channel": "channel", "severity": "category"}
    res = [
        TrendDataPoint(date=str(r.date), count=r.count, **{field_map.get(group_by, "category"): r.group_field})
        for r in rows
    ]
    analytics_cache.set(cache_key, res)
    return res


@router.get("/root-cause", response_model=RootCauseInsight)
async def get_root_cause(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"root_cause_{days}"
    cached = analytics_cache.get(cache_key)
    if cached is not None:
        return cached

    res = await generate_root_cause_insight(db, days)
    analytics_cache.set(cache_key, res)
    return res


@router.post("/cluster-rca", response_model=RootCauseInsight)
async def get_cluster_rca(
    complaint_ids: list[str] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    result = await generate_rca(db, limit=50, complaint_ids=complaint_ids)
    if not result:
        return RootCauseInsight(
            summary="No valid complaints found in cluster to analyze.",
            top_categories=[],
            top_products=[],
            recommendations=[]
        )
    return RootCauseInsight(**result)


@router.get("/weekly-summary")
async def get_weekly_summary(db: AsyncSession = Depends(get_db)):
    cache_key = "weekly_summary"
    cached = analytics_cache.get(cache_key)
    if cached is not None:
        return cached

    summary = await generate_weekly_summary(db)
    res = {"summary": summary}
    analytics_cache.set(cache_key, res)
    return res


@router.get("/complaint-clusters")
async def get_complaint_clusters(db: AsyncSession = Depends(get_db)):
    cache_key = "complaint_clusters"
    cached = analytics_cache.get(cache_key)
    if cached is not None:
        return cached

    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sqlalchemy.orm import selectinload
    from app.models.complaint import ComplaintEmbedding
    import asyncio

    result = await db.execute(
        select(Complaint)
        .join(ComplaintEmbedding, Complaint.id == ComplaintEmbedding.complaint_id)
        .options(selectinload(Complaint.embedding))
        .limit(1000)
    )
    complaints = result.scalars().all()

    if len(complaints) < 3:
        return []

    # Extract embedding vectors and necessary attributes
    embeddings = []
    complaint_data = []
    for c in complaints:
        embeddings.append(c.embedding.embedding)
        complaint_data.append({
            "id": str(c.id),
            "subject": c.subject or "Untitled Complaint",
            "body": c.body or "No description available.",
            "channel": c.channel or "web",
            "created_at": c.created_at.isoformat() if c.created_at else datetime.now(timezone.utc).isoformat(),
            "category": c.category or "general",
            "status": c.status,
            "severity": c.severity
        })

    def run_clustering(X_list, c_data):
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA

        X = np.array(X_list)
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X)

        x_min, x_max = X_pca[:, 0].min(), X_pca[:, 0].max()
        y_min, y_max = X_pca[:, 1].min(), X_pca[:, 1].max()
        x_range = (x_max - x_min) if (x_max - x_min) > 0 else 1.0
        y_range = (y_max - y_min) if (y_max - y_min) > 0 else 1.0

        X_scaled = np.zeros_like(X_pca)
        X_scaled[:, 0] = ((X_pca[:, 0] - x_min) / x_range) * 100
        X_scaled[:, 1] = ((X_pca[:, 1] - y_min) / y_range) * 100

        n_clusters = min(5, len(c_data))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X)

        cluster_themes = {}
        for i in range(n_clusters):
            indices = np.where(cluster_labels == i)[0]
            cluster_complaints = [c_data[idx] for idx in indices]
            cats = {}
            for cc in cluster_complaints:
                cats[cc["category"]] = cats.get(cc["category"], 0) + 1
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

        points = []
        for idx, c in enumerate(c_data):
            cluster_id = int(cluster_labels[idx])
            points.append({
                "id": c["id"],
                "subject": c["subject"],
                "body": c["body"],
                "channel": c["channel"],
                "created_at": c["created_at"],
                "category": c["category"],
                "status": c["status"],
                "severity": c["severity"],
                "x": float(X_scaled[idx, 0]),
                "y": float(X_scaled[idx, 1]),
                "cluster_id": cluster_id,
                "cluster_label": cluster_themes[cluster_id]
            })
        return points

    points = await asyncio.to_thread(run_clustering, embeddings, complaint_data)

    analytics_cache.set(cache_key, points)
    return points
