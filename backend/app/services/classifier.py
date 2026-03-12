import json
from google import genai
from app.config import get_settings
from app.schemas.schemas import ComplaintClassification

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

CLASSIFICATION_PROMPT = """You are a complaint classification AI for a financial services company. 
Analyze the following customer complaint and return a JSON object with these fields:

- category: one of [billing, product_defect, service_delay, account_access, delivery, refund, fraud, general]
- product: the specific product mentioned (e.g., "Credit Card", "Savings Account", "Mobile App", "Loan")
- severity: one of [critical, high, medium, low] based on urgency, financial impact, and customer distress
- sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
- sentiment_label: one of [positive, neutral, negative]
- key_issues: array of 2-4 short issue descriptions extracted from the complaint
- confidence: your confidence in this classification from 0.0 to 1.0
- regulatory_flags: array of flags if any apply: ["legal_mentioned", "regulator_mentioned", "ombudsman_mentioned", "lawsuit_mentioned", "discrimination_mentioned"]. Empty array if none.

Channel: {channel}
Complaint: {text}

Return ONLY the JSON object, no other text."""


async def classify_complaint(text: str, channel: str) -> ComplaintClassification:
    """Classify a complaint using the LLM."""
    if not client:
        return _fallback_classify(text)

    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=CLASSIFICATION_PROMPT.format(text=text, channel=channel),
        config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    )

    result = json.loads(response.text)
    return ComplaintClassification(**result)


def _fallback_classify(text: str) -> ComplaintClassification:
    """Simple rule-based fallback when no API key is available."""
    text_lower = text.lower()

    # Basic category detection
    category = "general"
    category_keywords = {
        "billing": ["bill", "charge", "payment", "invoice", "overcharged", "fee"],
        "product_defect": ["broken", "defect", "malfunction", "not working", "bug", "error"],
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
    if any(w in text_lower for w in ["urgent", "critical", "emergency", "immediately", "lawsuit", "legal"]):
        severity = "critical"
    elif any(w in text_lower for w in ["frustrated", "angry", "unacceptable", "terrible"]):
        severity = "high"

    # Basic sentiment
    negative_words = ["angry", "frustrated", "terrible", "worst", "hate", "awful", "unacceptable", "ridiculous"]
    score = -0.5 if any(w in text_lower for w in negative_words) else -0.2

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

    return ComplaintClassification(
        category=category,
        product=None,
        severity=severity,
        sentiment_score=score,
        sentiment_label="negative" if score < -0.3 else "neutral",
        key_issues=[],
        confidence=0.5,
        regulatory_flags=flags,
    )
