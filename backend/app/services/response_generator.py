import json
from google import genai
from app.config import get_settings
from app.schemas.schemas import GenerateResponseResult

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

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


REFINEMENT_PROMPT = """You are a customer service response drafting AI for a financial services company.
You need to refine an existing draft response based on custom instructions from the agent.

Original Complaint Details:
- Subject: {subject}
- Category: {category}
- Sentiment: {sentiment}
- Complaint Text: {body}

Current Draft Response:
{current_draft}

Refinement Instructions:
{instruction}

Adjust the draft response based on the refinement instructions, maintaining a professional and {tone} tone. Keep it concise (150-250 words) and address the customer's issues.

Also provide 2-3 updated suggested next-best actions for the agent.

Return a JSON object with:
- draft_text: the refined response text
- tone: the tone used
- suggested_actions: array of action strings

Return ONLY the JSON object."""


async def generate_response(
    complaint, 
    tone: str = "empathetic", 
    db = None, 
    instruction: str = None, 
    current_draft: str = None
) -> GenerateResponseResult:
    """Generate a draft response for a complaint."""
    if not client:
        return _fallback_response(complaint, tone)

    try:
        if instruction and current_draft:
            # Refinement prompt
            contents = REFINEMENT_PROMPT.format(
                subject=complaint.subject or "N/A",
                category=complaint.category or "general",
                sentiment=complaint.sentiment_label or "unknown",
                body=complaint.body,
                current_draft=current_draft,
                instruction=instruction,
                tone=tone,
            )
        else:
            # RAG context lookup
            knowledge_context = ""
            if db:
                try:
                    from app.models.knowledge import KnowledgeDocument
                    from app.services.duplicate_detector import generate_embedding
                    from sqlalchemy import text
                    
                    embedding_vector = await generate_embedding(complaint.body)
                    if embedding_vector:
                        sql = text("""
                            SELECT title, content
                            FROM knowledge_documents
                            ORDER BY embedding <=> :query_embedding
                            LIMIT 2
                        """)
                        result = await db.execute(sql, {"query_embedding": str(embedding_vector)})
                        rows = result.all()
                        if rows:
                            kb_texts = []
                            for r in rows:
                                kb_texts.append(f"Policy Title: {r.title}\nPolicy Content:\n{r.content}")
                            knowledge_context = "\n\nUse the following company policies to guide your resolution steps:\n" + "\n---\n".join(kb_texts)
                except Exception as e:
                    print(f"Error loading knowledge base context for RAG: {e}")

            contents = RESPONSE_PROMPT.format(
                subject=complaint.subject or "N/A",
                category=complaint.category or "general",
                severity=complaint.severity,
                sentiment=complaint.sentiment_label or "unknown",
                body=complaint.body,
                tone=tone,
            ) + knowledge_context

        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
            },
        )

        result = json.loads(response.text)
        return GenerateResponseResult(**result)
    except Exception as e:
        print(f"Gemini API error during response generation: {e}. Using fallback templates.")
        return _fallback_response(complaint, tone)


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
