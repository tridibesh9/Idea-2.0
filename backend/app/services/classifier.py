import json
import base64
from google import genai
from app.config import get_settings
from app.schemas.schemas import ComplaintClassification
from app.services.pii_redactor import pii_redactor
#
settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

CLASSIFICATION_PROMPT = """You are a complaint classification AI for a financial services company. 
Analyze the following customer complaint (and any attached image, if provided) and return a JSON object with these fields:

- category: one of [billing, product_defect, service_delay, account_access, delivery, refund, fraud, general]
- product: the specific product mentioned (e.g., "Credit Card", "Savings Account", "Mobile App", "Loan")
- severity: one of [critical, high, medium, low] based on urgency, financial impact, and customer distress
- sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
- sentiment_label: one of [positive, neutral, negative]
- key_issues: array of 2-4 short issue descriptions extracted from the complaint text or image
- confidence: your confidence in this classification from 0.0 to 1.0
- regulatory_flags: array of flags if any apply: ["legal_mentioned", "regulator_mentioned", "ombudsman_mentioned", "lawsuit_mentioned", "discrimination_mentioned"]. Empty array if none.
- next_best_action: A concise sentence suggesting the best action for the agent to take (e.g., "Issue full refund immediately", "Escalate to technical support team").
- subject: A concise, professional 3-6 word summary of the complaint (e.g., "Incorrect Late Fee Applied", "Mobile App Login Crash").

Channel: {channel}
Complaint: {text}

Return ONLY the JSON object, no other text."""


async def classify_complaint(text: str, channel: str, image_base64: str | None = None) -> ComplaintClassification:
    """Classify a complaint using the LLM, with PII redaction and optional multimodal image support."""
    # 1. PII Redaction Pipeline (Enterprise compliance)
    safe_text, _ = pii_redactor.redact(text)

    if not client:
        return _fallback_classify(safe_text)

    # 2. Prepare Contents (Text + Optional Image)
    prompt = CLASSIFICATION_PROMPT.format(text=safe_text, channel=channel)
    contents = [prompt]

    if image_base64:
        try:
            # The base64 string might come with a prefix like "data:image/jpeg;base64,...", so we strip it.
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
                
            contents.append(
                genai.types.Part.from_bytes(
                    data=base64.b64decode(image_base64),
                    mime_type="image/jpeg",
                )
            )
        except Exception as e:
            # If image parsing fails, fallback to handling just the text
            print(f"Error handling image part: {e}")

    # 3. Model Generation
    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config={
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )

        result = json.loads(response.text)
        return ComplaintClassification(**result)
    except Exception as e:
        import logging
        logger = logging.getLogger("classifier")
        logger.warning(f"Failed to classify complaint with Gemini, using fallback: {e}")
        return _fallback_classify(text)


def _fallback_classify(text: str) -> ComplaintClassification:
    """Simple rule-based fallback when no API key is available."""
    text_lower = text.lower()

    # Basic category detection
    category = "general"
    category_keywords = {
        "billing": ["bill", "charge", "payment", "invoice", "overcharged", "fee"],
        "product_defect": ["broken", "defect", "malfunction", "not working", "bug", "error", "freezing"],
        "service_delay": ["delay", "slow", "waiting", "late", "took too long"],
        "account_access": ["login", "password", "locked", "access", "account"],
        "delivery": ["delivery", "shipping", "package", "arrived", "missing"],
        "refund": ["refund", "return", "money back", "reimburse"],
        "fraud": ["fraud", "unauthorized", "stolen", "hack"],
    }
    for cat, keywords in category_keywords.items():
        if any(kw in text_lower for kw in keywords):
            category = cat
            break

    # Basic severity
    severity = "medium"
    if any(w in text_lower for w in ["urgent", "critical", "emergency", "immediately", "lawsuit", "legal", "fix immediately", "transact"]):
        severity = "critical"
    elif any(w in text_lower for w in ["frustrated", "angry", "unacceptable", "terrible"]):
        severity = "high"

    # Basic sentiment
    negative_words = ["angry", "frustrated", "terrible", "worst", "hate", "awful", "unacceptable", "ridiculous", "not working", "freezing", "immediately"]
    score = -0.5 if any(w in text_lower for w in negative_words) else -0.1
    if severity == "critical":
        score = -0.8
    if severity == "high" and score > -0.5:
        score = -0.6

    # Regulatory flags
    flags = []
    if any(w in text_lower for w in ["legal", "lawyer", "attorney"]):
        flags.append("legal_mentioned")
    if any(w in text_lower for w in ["regulator", "regulatory"]):
        flags.append("regulator_mentioned")
    if "ombudsman" in text_lower:
        flags.append("ombudsman_mentioned")
    if "lawsuit" in text_lower:
        flags.append("lawsuit_mentioned")
    words = text.split()
    fallback_subject = " ".join(words[:5]) + ("..." if len(words) > 5 else "")

    return ComplaintClassification(
        category=category,
        product=None,
        severity=severity,
        sentiment_score=score,
        sentiment_label="negative" if score <= -0.3 else "neutral",
        key_issues=[],
        confidence=0.5,
        regulatory_flags=flags,
        next_best_action="Investigate issue and respond to customer.",
        subject=fallback_subject
    )
