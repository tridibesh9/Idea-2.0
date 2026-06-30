import uuid
from google import genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.complaint import Complaint

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

HANDOVER_PROMPT = """You are an AI assistant generating an Escalation Handover Report for a human agent.
Summarize the following complaint details, extracted entities, and conversation history into a concise, professional report.
The report should include:
1. Executive Summary (1-2 sentences)
2. Key Entities (Customer IDs, Order Numbers, etc.)
3. Sentiment Shift (e.g., started Neutral, became Angry)
4. AI Actions Attempted (if any AI responses were sent)
5. Recommended Next Best Action for the human agent

Complaint Details:
Subject: {subject}
Category: {category}
Severity: {severity}
Current Sentiment: {sentiment}
Next Best Action (suggested by AI): {nba}

Entities:
{entities}

Timeline (Messages):
{timeline}

Return the report formatted in Markdown.
"""

async def generate_handover_report(complaint_id: uuid.UUID, db: AsyncSession) -> str | None:
    if not client:
        return "AI Handover Report unavailable (No API Key)"
        
    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.entities), selectinload(Complaint.messages))
        .where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        return None
        
    from app.services.pii_redactor import pii_redactor
    
    entities_str = "\n".join([f"- {e.entity_type}: {e.entity_value}" for e in complaint.entities])
    
    timeline_messages = []
    for m in complaint.messages:
        safe_content, _ = pii_redactor.redact(m.content)
        timeline_messages.append(f"[{m.created_at}] {m.sender_type.upper()}: {safe_content}")
    timeline_str = "\n".join(timeline_messages)
    
    prompt = HANDOVER_PROMPT.format(
        subject=complaint.subject,
        category=complaint.category,
        severity=complaint.severity,
        sentiment=complaint.sentiment_label,
        nba=complaint.next_best_action,
        entities=entities_str if entities_str else "None extracted",
        timeline=timeline_str
    )
    
    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt],
        )
        return response.text
    except Exception as e:
        print(f"Failed to generate handover report: {e}")
        return "Handover report generation failed."
