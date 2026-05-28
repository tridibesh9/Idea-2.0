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

    def redact(self, text: str) -> tuple[str, dict]:
        if not text:
            return text, {}
            
        redacted_text = text
        extracted_entities = {}
        for token, pattern in self.patterns.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                # Store the matches under the token type (e.g., CREDIT_CARD_REDACTED: ["1234-...", "5678-..."])
                # We'll just store unique ones if there are multiples.
                # If a match is a tuple (due to capture groups like in PHONE), we join it
                processed_matches = []
                for match in matches:
                    if isinstance(match, tuple):
                        processed_matches.append("-".join(m for m in match if m))
                    else:
                        processed_matches.append(match)
                
                if token not in extracted_entities:
                    extracted_entities[token] = []
                extracted_entities[token].extend(list(set(processed_matches)))

            redacted_text = re.sub(pattern, f"[{token}]", redacted_text)
            
        return redacted_text, extracted_entities

pii_redactor = PIIRedactor()
