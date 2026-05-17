import re

class PIIRedactor:
    """
    A lightweight, regex-based NLP pre-processor to redact Personally Identifiable Information (PII) 
    before sending data to external LLMs, ensuring compliance with privacy regulations (GDPR, PCI-DSS).
    """
    def __init__(self):
        # Regular expressions for common PII
        self.patterns = {
            "CREDIT_CARD_REDACTED": r"\b(?:\d[ -]*?){13,16}\b",
            "EMAIL_REDACTED": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
            "PHONE_REDACTED": r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b",
            "SSN_REDACTED": r"\b\d{3}-\d{2}-\d{4}\b"
        }

    def redact(self, text: str) -> str:
        if not text:
            return text
            
        redacted_text = text
        for token, pattern in self.patterns.items():
            redacted_text = re.sub(pattern, f"[{token}]", redacted_text)
            
        return redacted_text

pii_redactor = PIIRedactor()
