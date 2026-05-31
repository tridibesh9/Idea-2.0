"""Email sending service using Resend API."""

import logging
from typing import Optional, List
import httpx
import os
import uuid

from app.config import get_settings

logger = logging.getLogger("email_sender")
settings = get_settings()


class EmailSender:
    """Handles sending emails via Resend."""

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.support_email = settings.SUPPORT_EMAIL
        self.support_name = settings.SUPPORT_NAME
        self.is_mock_mode = not self.api_key or self.api_key == ""

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        references: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email via Resend API.

        Args:
            recipient: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            reply_to: Optional reply-to address
            cc: Optional list of CC addresses
            references: Optional References header for threading
            in_reply_to: Optional In-Reply-To header for threading

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.is_mock_mode:
                os.makedirs("mock_emails/sent", exist_ok=True)
                filename = f"sent_{uuid.uuid4().hex[:8]}.txt"
                filepath = os.path.join("mock_emails/sent", filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"To: {recipient}\n")
                    f.write(f"Subject: {subject}\n")
                    if in_reply_to:
                        f.write(f"In-Reply-To: {in_reply_to}\n")
                    if references:
                        f.write(f"References: {references}\n")
                    f.write(f"\nBody:\n{body_text}\n")
                logger.info(f"[MOCK] Outgoing email saved to {filepath} successfully")
                return True

            payload = {
                "from": f"{self.support_name} <{self.support_email}>",
                "to": [recipient],
                "subject": subject,
                "text": body_text,
            }

            if body_html:
                payload["html"] = body_html
            
            if reply_to:
                payload["reply_to"] = reply_to
                
            if cc:
                payload["cc"] = cc

            headers = {}
            if in_reply_to:
                headers["In-Reply-To"] = in_reply_to
            if references:
                headers["References"] = references
                
            if headers:
                payload["headers"] = headers

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code >= 400:
                    logger.error(f"Resend API error: {response.text}")
                    return False

            logger.info(f"Email sent successfully to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False


async def send_reply_email(
    recipient: str,
    subject: str,
    body_text: str,
    original_complaint_id: str,
    original_message_id: Optional[str] = None,
    original_references: Optional[str] = None,
) -> bool:
    """
    Send a reply email for a complaint (convenience function).

    Args:
        recipient: Customer email address
        subject: Email subject (typically prefixed with "Re: ")
        body_text: Reply text
        original_complaint_id: Complaint ID for reference
        original_message_id: Original email Message-ID for threading
        original_references: Original References header for threading

    Returns:
        True if successful, False otherwise
    """
    sender = EmailSender()

    # Ensure subject has Re: prefix
    if not subject.startswith("Re: "):
        subject = f"Re: {subject}"

    # Add complaint reference to subject if not already present
    if f"[Ticket #{original_complaint_id}]" not in subject:
        subject = f"[Ticket #{original_complaint_id}] {subject}"

    # Add footer with ticket reference
    footer = f"\n\n---\nTicket Reference: #{original_complaint_id}\nThis is an automated response. Please do not reply above this line."
    body_text = body_text + footer

    return await sender.send_email(
        recipient=recipient,
        subject=subject,
        body_text=body_text,
        reply_to=settings.SUPPORT_EMAIL,
        in_reply_to=original_message_id,
        references=original_references,
    )
