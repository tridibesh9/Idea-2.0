import json
from datetime import datetime, timedelta, timezone
from google import genai
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.complaint import Complaint
from app.schemas.schemas import RootCauseInsight

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None


async def _get_complaint_stats(db: AsyncSession, days: int) -> dict:
    """Aggregate complaint stats for AI analysis."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Category counts
    cat_result = await db.execute(
        select(Complaint.category, func.count(Complaint.id))
        .where(Complaint.created_at >= since)
        .group_by(Complaint.category)
        .order_by(func.count(Complaint.id).desc())
    )
    categories = [{"category": r[0] or "uncategorized", "count": r[1]} for r in cat_result.all()]

    # Product counts
    prod_result = await db.execute(
        select(Complaint.product, func.count(Complaint.id))
        .where(Complaint.created_at >= since, Complaint.product.isnot(None))
        .group_by(Complaint.product)
        .order_by(func.count(Complaint.id).desc())
        .limit(10)
    )
    products = [{"product": r[0], "count": r[1]} for r in prod_result.all()]

    # Severity counts
    sev_result = await db.execute(
        select(Complaint.severity, func.count(Complaint.id))
        .where(Complaint.created_at >= since)
        .group_by(Complaint.severity)
    )
    severities = {r[0]: r[1] for r in sev_result.all()}

    # Average sentiment
    avg_sent = (await db.execute(
        select(func.avg(Complaint.sentiment_score)).where(Complaint.created_at >= since)
    )).scalar()

    total = sum(c["count"] for c in categories)

    return {
        "period_days": days,
        "total_complaints": total,
        "categories": categories,
        "products": products,
        "severities": severities,
        "avg_sentiment": round(float(avg_sent), 2) if avg_sent else None,
    }


async def generate_root_cause_insight(db: AsyncSession, days: int = 30) -> RootCauseInsight:
    """Generate AI-powered root cause insights."""
    stats = await _get_complaint_stats(db, days)

    if not client:
        return RootCauseInsight(
            summary=f"In the last {days} days, {stats['total_complaints']} complaints were received. "
                    f"Top category: {stats['categories'][0]['category'] if stats['categories'] else 'N/A'}.",
            top_categories=stats["categories"][:5],
            top_products=stats["products"][:5],
            recommendations=["Review top complaint categories", "Investigate recurring product issues"],
        )

    prompt = f"""Analyze these customer complaint statistics and provide root cause insights:

Stats (last {days} days):
{json.dumps(stats, indent=2)}

Return a JSON object with:
- summary: a 2-3 sentence executive summary of complaint trends and likely root causes
- top_categories: the top 5 categories with counts (pass through from input)
- top_products: the top 5 products with counts (pass through from input)
- recommendations: 3-5 actionable recommendations to reduce complaints

Return ONLY the JSON object."""

    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.3,
            "response_mime_type": "application/json",
        },
    )

    result = json.loads(response.text)
    return RootCauseInsight(**result)


async def generate_weekly_summary(db: AsyncSession) -> str:
    """Generate a weekly AI summary of complaint data."""
    stats = await _get_complaint_stats(db, 7)

    if not client:
        return (
            f"Weekly Summary: {stats['total_complaints']} complaints received. "
            f"Categories: {', '.join(c['category'] + ' (' + str(c['count']) + ')' for c in stats['categories'][:3])}. "
            f"Average sentiment: {stats['avg_sentiment']}."
        )

    prompt = f"""Write a concise weekly complaint summary report (3-4 paragraphs) based on these stats:

{json.dumps(stats, indent=2)}

Cover: volume trends, top issues, severity distribution, and actionable recommendations.
Write in a professional tone suitable for a management report."""

    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.4,
        },
    )

    return response.text
