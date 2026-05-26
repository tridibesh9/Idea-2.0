"""Email parsing service for extracting structured data from raw email messages."""

import logging
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from email.header import decode_header

logger = logging.getLogger("email_parser")


@dataclass
class ParsedEmail:
    """Structured representation of a parsed email."""

    from_email: str
    from_name: str
    subject: str
    body_text: str
    body_html: Optional[str] = None
    date: Optional[datetime] = None
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: list[str] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []


def decode_email_header(header_value: str) -> str:
    """Safely decode email header values that may be encoded."""
    if not header_value:
        return ""

    try:
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                decoded_parts.append(str(part))
        return "".join(decoded_parts).strip()
    except Exception as e:
        logger.warning(f"Failed to decode header: {e}")
        return str(header_value).strip()


def extract_text_from_html(html: str) -> str:
    """Simple extraction of text content from HTML email body."""
    if not html:
        return ""

    # Remove common HTML tags
    text = re.sub(r"<[^>]+>", "", html)
    # Decode HTML entities
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&amp;", "&")
    # Remove multiple spaces/newlines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def sanitize_html(html: str) -> str:
    """Basic sanitization of HTML to prevent injection attacks."""
    if not html:
        return ""

    # Remove potentially dangerous tags and attributes
    dangerous_tags = ["script", "iframe", "object", "embed", "form"]
    for tag in dangerous_tags:
        html = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.IGNORECASE | re.DOTALL
        )
        html = re.sub(rf"<{tag}[^>]*/>", "", html, flags=re.IGNORECASE)

    # Remove event handlers
    html = re.sub(
        r'\s*on\w+\s*=\s*["\']?[^"\'\s>]*["\']?', "", html, flags=re.IGNORECASE
    )

    return html


def extract_ticket_id_from_subject(subject: str) -> Optional[str]:
    """Extract ticket ID from subject line (e.g., [Ticket #UUID] or Re: [Ticket #UUID])."""
    if not subject:
        return None

    # Look for pattern like [Ticket #<uuid-like-string>]
    match = re.search(r"\[Ticket\s+#([a-f0-9\-]+)\]", subject, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_email_address(email_string: str) -> str:
    """Extract email address from "Name <email@example.com>" format."""
    if not email_string:
        return ""

    # Try to extract from angle brackets
    match = re.search(r"<([^>]+)>", email_string)
    if match:
        return match.group(1).strip()

    return email_string.strip()


def parse_email_message(raw_email_bytes: bytes) -> ParsedEmail:
    """
    Parse a raw email message into structured data.

    Args:
        raw_email_bytes: Raw email data (bytes)

    Returns:
        ParsedEmail object with extracted information
    """
    try:
        msg = message_from_bytes(raw_email_bytes)

        # Extract basic headers
        from_header = msg.get("From", "")
        subject = decode_email_header(msg.get("Subject", "No Subject"))
        message_id = msg.get("Message-ID", "")
        in_reply_to = msg.get("In-Reply-To", "")
        references = msg.get("References", "").split() if msg.get("References") else []

        # Parse from address and name
        from_email = extract_email_address(from_header)
        from_name = from_header.replace(f"<{from_email}>", "").strip() or from_email
        if not from_name or from_name == from_email:
            from_name = from_email.split("@")[0].title()

        # Parse date
        date_header = msg.get("Date", "")
        date = None
        try:
            date = parsedate_to_datetime(date_header)
        except (TypeError, ValueError):
            logger.warning(f"Could not parse date: {date_header}")

        # Extract body content
        body_text = ""
        body_html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()

                try:
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body_text = payload.decode(charset, errors="replace")
                    elif content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body_html = sanitize_html(
                            payload.decode(charset, errors="replace")
                        )
                except Exception as e:
                    logger.warning(f"Error extracting {content_type}: {e}")
        else:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            content_type = msg.get_content_type()

            if content_type == "text/html":
                body_html = sanitize_html(payload.decode(charset, errors="replace"))
            else:
                body_text = payload.decode(charset, errors="replace")

        # If we have HTML but no plain text, extract text from HTML
        if body_html and not body_text:
            body_text = extract_text_from_html(body_html)

        # Clean up body text
        body_text = body_text.strip()

        # Remove quoted content from previous emails (common pattern)
        if "\n\nOn " in body_text and " wrote:" in body_text:
            body_text = body_text.split("\n\nOn ")[0].strip()

        return ParsedEmail(
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            date=date,
            message_id=message_id,
            in_reply_to=in_reply_to,
            references=references,
        )

    except Exception as e:
        logger.error(f"Error parsing email: {e}")
        raise
