"""Email sending service using SMTP (Python equivalent of Nodemailer)."""

import logging
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import aiosmtplib

from app.config import get_settings

logger = logging.getLogger("email_sender")
settings = get_settings()


class EmailSender:
    """Handles sending emails via SMTP."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.email = settings.SMTP_EMAIL
        self.password = settings.SMTP_PASSWORD
        self.support_email = settings.SUPPORT_EMAIL
        self.support_name = settings.SUPPORT_NAME

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
        Send an email via SMTP.

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
            if not self.email or not self.password:
                logger.error("SMTP credentials not configured")
                return False

            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = formataddr((self.support_name, self.support_email))
            msg["To"] = recipient
            msg["Subject"] = subject

            if cc:
                msg["Cc"] = ", ".join(cc)

            if reply_to:
                msg["Reply-To"] = reply_to

            # Add threading headers
            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to

            if references:
                msg["References"] = references

            # Attach text part
            part1 = MIMEText(body_text, "plain", "utf-8")
            msg.attach(part1)

            # Attach HTML part if provided
            if body_html:
                part2 = MIMEText(body_html, "html", "utf-8")
                msg.attach(part2)

            # Send via SMTP
            use_tls = self.port == 465
            start_tls = self.port == 587
            async with aiosmtplib.SMTP(
                hostname=self.host, 
                port=self.port,
                use_tls=use_tls,
                start_tls=start_tls
            ) as smtp:
                await smtp.login(self.email, self.password)
                recipients = [recipient]
                if cc:
                    recipients.extend(cc)
                await smtp.send_message(msg)

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
