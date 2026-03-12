import json
from openai import AsyncOpenAI
from app.config import get_settings
from app.schemas.schemas import GenerateResponseResult

settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

RESPONSE_PROMPT = """You are a customer service response drafting AI for a financial services company.
Draft a professional response to the following customer complaint.

Complaint Details:
- Subject: {subject}
- Category: {category}
- Severity: {severity}
- Sentiment: {sentiment}
- Complaint Text: {body}

Instructions:
- Tone: {tone}
- Acknowledge the customer's concern
- Address the specific issues raised
- Provide clear next steps or resolution
- Be concise but thorough (150-250 words)

Also provide 2-3 suggested next-best actions for the agent.

Return a JSON object with:
- draft_text: the response text
- tone: the tone used
- suggested_actions: array of action strings

Return ONLY the JSON object."""


async def generate_response(complaint, tone: str = "empathetic") -> GenerateResponseResult:
    """Generate a draft response for a complaint."""
    if not client:
        return _fallback_response(complaint, tone)

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful customer service response generator. Always respond with valid JSON only."},
            {
                "role": "user",
                "content": RESPONSE_PROMPT.format(
                    subject=complaint.subject or "N/A",
                    category=complaint.category or "general",
                    severity=complaint.severity,
                    sentiment=complaint.sentiment_label or "unknown",
                    body=complaint.body,
                    tone=tone,
                ),
            },
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return GenerateResponseResult(**result)


def _fallback_response(complaint, tone: str) -> GenerateResponseResult:
    """Fallback template when no API key is available."""
    templates = {
        "formal": f"Dear Customer,\n\nThank you for contacting us regarding your concern about {complaint.category or 'your issue'}. We have received your complaint (Reference ID: {complaint.id}) and our team is reviewing it with high priority.\n\nWe understand the importance of this matter and will provide you with an update within the next 24 hours.\n\nSincerely,\nCustomer Support Team",
        "empathetic": f"Hi there,\n\nI'm sorry to hear about your experience with {complaint.category or 'our service'}. That's definitely not the experience we want for our customers, and I completely understand your frustration.\n\nI've flagged your case (Ref: {complaint.id}) for priority review, and I'll personally ensure we get this resolved for you as quickly as possible.\n\nLet me look into this right away and get back to you shortly.\n\nWarm regards,\nCustomer Support Team",
        "neutral": f"Hello,\n\nThank you for reaching out about {complaint.category or 'your concern'}. Your complaint (Ref: {complaint.id}) has been logged and assigned for review.\n\nOur team will investigate and respond within the SLA timeframe. If you have additional details, please reply to this thread.\n\nBest regards,\nCustomer Support Team",
    }
    return GenerateResponseResult(
        draft_text=templates.get(tone, templates["empathetic"]),
        tone=tone,
        suggested_actions=[
            "Review customer's account history",
            "Check for related open complaints",
            "Escalate to supervisor if unresolved within SLA",
        ],
    )
