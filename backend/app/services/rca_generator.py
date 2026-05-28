import json
from google import genai
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.complaint import Complaint

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

RCA_PROMPT = """You are an expert Data Analyst and Root Cause Analysis AI for a Customer Support center.
Analyze the following batch of recent customer complaints.
Look for common patterns, underlying issues, and generate a Root Cause Analysis (RCA) report.

Complaints Data:
{complaints_data}

Return ONLY a valid JSON object matching this schema:
{{
  "summary": "A 2-3 sentence executive summary of the root cause.",
  "top_categories": [{{"name": "category name", "count": int}}],
  "top_products": [{{"name": "product name", "count": int}}],
  "recommendations": ["Actionable recommendation 1", "Actionable recommendation 2"]
}}
"""

async def generate_rca(db: AsyncSession, limit: int = 50) -> dict | None:
    if not client:
        return None
        
    result = await db.execute(
        select(Complaint)
        .order_by(desc(Complaint.created_at))
        .limit(limit)
    )
    complaints = result.scalars().all()
    
    if not complaints:
        return None
        
    # Prepare concise data for LLM
    data = []
    for c in complaints:
        data.append({
            "subject": c.subject,
            "category": c.category,
            "product": c.product,
            "severity": c.severity,
            "sentiment": c.sentiment_label,
            "key_issues": c.key_issues
        })
        
    prompt = RCA_PROMPT.format(complaints_data=json.dumps(data))
    
    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt],
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to generate RCA: {e}")
        return None
