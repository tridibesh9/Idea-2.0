import json
from google import genai
from app.config import get_settings

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

ENTITY_EXTRACTION_PROMPT = """You are a precise data extraction AI. 
Extract business entities from the following customer complaint text.
The text may have sensitive PII already redacted (e.g., [CREDIT_CARD_REDACTED]).
Extract ONLY non-sensitive business entities like:
- CUSTOMER_ID
- ORDER_NUMBER
- PRODUCT_CODE
- LOCATION
- TRACKING_NUMBER

If none are found, return an empty list.

Return ONLY a JSON array of objects, with each object having exactly two keys: "entity_type" and "entity_value".
Example:
[
  {"entity_type": "ORDER_NUMBER", "entity_value": "ORD-12345"},
  {"entity_type": "PRODUCT_CODE", "entity_value": "XYZ-99"}
]

Complaint: {text}
"""

async def extract_entities(text: str) -> list[dict]:
    """Extract business entities from text using LLM."""
    if not client or not text:
        return []

    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[ENTITY_EXTRACTION_PROMPT.format(text=text)],
            config={
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )
        result = json.loads(response.text)
        if isinstance(result, list):
            return result
        return []
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return []
