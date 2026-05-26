"""Inbound email listener service using IMAP."""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

from imap_tools import MailBox, MailBoxUnencrypted, AND
from sqlalchemy import select

from app.config import get_settings
from app.services.email_parser import (
    parse_email_message,
    extract_ticket_id_from_subject,
)
from app.models.complaint import Complaint, ComplaintMessage, ComplaintEmbedding
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.services.classifier import classify_complaint
from app.services.duplicate_detector import generate_embedding
from app.database import async_session

logger = logging.getLogger("email_listener")
settings = get_settings()

SLA_HOURS = {"critical": 4, "high": 8, "medium": 24, "low": 72}


class EmailListener:
    """Manages IMAP connection and monitors for incoming emails."""

    def __init__(self):
        self.host = settings.IMAP_HOST
        self.port = settings.IMAP_PORT
        self.email = settings.IMAP_EMAIL
        self.password = settings.IMAP_PASSWORD
        self.mailbox = "INBOX"
        self.is_running = False
        self._broadcast_callback: Optional[Callable] = None
        self._executor = ThreadPoolExecutor(max_workers=1)

    def set_broadcast_callback(self, callback: Callable):
        """Set callback function for WebSocket broadcasts."""
        self._broadcast_callback = callback

    async def connect(self):
        """Establish IMAP connection."""
        try:
            # Connect to IMAP server
            def _connect():
                if self.port == 993:
                    return MailBox(self.host, port=self.port).login(self.email, self.password)
                elif self.port == 143:
                    try:
                        return MailBoxTls(self.host, port=self.port).login(self.email, self.password)
                    except Exception:
                        return MailBoxUnencrypted(self.host, port=self.port).login(self.email, self.password)
                else:
                    return MailBoxUnencrypted(self.host, port=self.port).login(self.email, self.password)
            
            mailbox = await asyncio.get_event_loop().run_in_executor(
                self._executor, _connect
            )
            logger.info(f"Connected to IMAP server {self.host}")
            return mailbox
        except Exception as e:
            logger.error(f"Failed to connect to IMAP: {e}")
            raise

    async def fetch_unseen_emails(self, mailbox) -> list[tuple[str, bytes]]:
        """Fetch all unseen emails from inbox."""
        try:
            # Search for unseen messages
            def _fetch():
                emails = []
                try:
                    # Fetch all unseen messages
                    for msg in mailbox.fetch(AND(seen=False)):
                        try:
                            # Get the raw email bytes
                            email_bytes = msg.obj.as_bytes()
                            emails.append((msg.uid, email_bytes))
                        except Exception as e:
                            logger.warning(
                                f"Failed to get email bytes for {msg.uid}: {e}"
                            )
                except Exception as e:
                    logger.warning(f"Failed to fetch emails: {e}")
                return emails

            emails = await asyncio.get_event_loop().run_in_executor(
                self._executor, _fetch
            )
            logger.info(f"Fetched {len(emails)} unseen emails")
            return emails

        except Exception as e:
            logger.error(f"Failed to fetch unseen emails: {e}")
            return []

    async def mark_as_seen(self, mailbox, uid: str):
        """Mark email as seen after processing."""
        try:

            def _mark():
                mailbox.flag([uid], "+FLAGS", "\\Seen", silent=True)

            await asyncio.get_event_loop().run_in_executor(self._executor, _mark)
        except Exception as e:
            logger.warning(f"Failed to mark email {uid} as seen: {e}")

    async def process_email(self, email_bytes: bytes, uid: str) -> Optional[uuid.UUID]:
        """
        Process a single email and create/update complaint in database.

        Args:
            email_bytes: Raw email data
            uid: IMAP UID

        Returns:
            Complaint ID if successful, None otherwise
        """
        try:
            # Parse email
            parsed = parse_email_message(email_bytes)

            # Get or create customer
            customer = None
            async with async_session() as db:
                result = await db.execute(
                    select(Customer).where(Customer.email == parsed.from_email)
                )
                customer = result.scalar_one_or_none()

                if not customer:
                    customer = Customer(
                        name=parsed.from_name,
                        email=parsed.from_email,
                    )
                    db.add(customer)
                    await db.flush()

                # Check if this is a reply to an existing complaint
                complaint = None
                ticket_id = extract_ticket_id_from_subject(parsed.subject)

                if ticket_id:
                    try:
                        # Try to parse UUID from ticket ID
                        result = await db.execute(
                            select(Complaint).where(
                                Complaint.id == uuid.UUID(ticket_id)
                            )
                        )
                        complaint = result.scalar_one_or_none()
                    except (ValueError, TypeError):
                        pass

                # If not found by ticket ID, check In-Reply-To header
                if not complaint and parsed.in_reply_to:
                    result = await db.execute(
                        select(ComplaintMessage)
                        .where(
                            ComplaintMessage.__table__.c.content.contains(
                                parsed.in_reply_to
                            )
                        )
                        .limit(1)
                    )
                    msg = result.scalar_one_or_none()
                    if msg:
                        complaint = msg.complaint

                # If not a reply, create new complaint
                if not complaint:
                    complaint = Complaint(
                        channel="email",
                        external_id=parsed.message_id,
                        subject=parsed.subject,
                        body=parsed.body_text,
                        customer_id=customer.id,
                        status="new",
                    )
                    db.add(complaint)
                    await db.flush()

                    # AI Classification
                    classification = await classify_complaint(parsed.body_text, "email")
                    complaint.category = classification.category
                    complaint.product = classification.product
                    complaint.severity = classification.severity
                    complaint.sentiment_score = classification.sentiment_score
                    complaint.sentiment_label = classification.sentiment_label
                    complaint.key_issues = json.dumps(classification.key_issues)
                    complaint.ai_confidence_score = classification.confidence
                    complaint.regulatory_flags = json.dumps(
                        classification.regulatory_flags
                    )

                    # Set SLA deadline
                    hours = SLA_HOURS.get(classification.severity, 24)
                    complaint.sla_deadline = datetime.now(timezone.utc) + timedelta(
                        hours=hours
                    )

                    # Generate embedding
                    try:
                        embedding_vector = await generate_embedding(parsed.body_text)
                        if embedding_vector:
                            from app.models.complaint import ComplaintEmbedding

                            emb = ComplaintEmbedding(
                                complaint_id=complaint.id, embedding=embedding_vector
                            )
                            db.add(emb)
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding: {e}")

                    # Create audit log
                    audit = AuditLog(
                        complaint_id=complaint.id,
                        action="email_received",
                        performed_by="system",
                        details=json.dumps(
                            {
                                "from": parsed.from_email,
                                "message_id": parsed.message_id,
                                "classification": classification.model_dump(),
                            }
                        ),
                    )
                    db.add(audit)
                else:
                    # Update existing complaint
                    complaint.updated_at = datetime.now(timezone.utc)
                    complaint.status = "open"

                # Add message to complaint
                msg = ComplaintMessage(
                    complaint_id=complaint.id,
                    sender_type="customer",
                    sender_name=parsed.from_name,
                    content=parsed.body_text,
                    channel="email",
                    created_at=parsed.date or datetime.now(timezone.utc),
                )
                db.add(msg)

                # Create audit log for new message
                if complaint.id:
                    audit = AuditLog(
                        complaint_id=complaint.id,
                        action="email_message_added",
                        performed_by="system",
                        details=json.dumps(
                            {
                                "from": parsed.from_email,
                                "subject": parsed.subject,
                            }
                        ),
                    )
                    db.add(audit)

                await db.commit()

                # Broadcast to WebSocket if callback is set
                if self._broadcast_callback:
                    try:
                        await self._broadcast_callback(
                            {
                                "type": "new_complaint",
                                "complaint_id": str(complaint.id),
                                "subject": complaint.subject,
                                "category": complaint.category,
                                "severity": complaint.severity,
                                "customer": parsed.from_name,
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to broadcast: {e}")

                logger.info(
                    f"Email processed: {parsed.subject} from {parsed.from_email}"
                )
                return complaint.id

        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return None

    async def run(self):
        """Main loop for listening to emails."""
        if not self.email or not self.password:
            logger.warning("Email credentials not configured, listener disabled")
            return

        self.is_running = True
        connection_retries = 0
        max_retries = 5

        while self.is_running:
            mailbox = None
            try:
                # Connect to IMAP
                mailbox = await self.connect()
                connection_retries = 0

                # Monitor for emails
                while self.is_running:
                    # Fetch unseen emails
                    emails = await self.fetch_unseen_emails(mailbox)

                    # Process each email
                    for uid, email_bytes in emails:
                        try:
                            await self.process_email(email_bytes, uid)
                            await self.mark_as_seen(mailbox, uid)
                        except Exception as e:
                            logger.error(f"Error processing email {uid}: {e}")

                    # Wait before checking again
                    await asyncio.sleep(settings.EMAIL_CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Email listener error: {e}")
                connection_retries += 1

                if connection_retries > max_retries:
                    logger.error("Max retries reached, stopping listener")
                    self.is_running = False
                else:
                    # Wait before retrying
                    wait_time = min(60 * connection_retries, 300)  # Max 5 minutes
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

            finally:
                if mailbox:
                    try:

                        def _close():
                            mailbox.logout()

                        await asyncio.get_event_loop().run_in_executor(
                            self._executor, _close
                        )
                    except Exception:
                        pass

    async def stop(self):
        """Stop the email listener."""
        self.is_running = False
        if self._executor:
            self._executor.shutdown(wait=False)
        logger.info("Email listener stopped")


# Global instance
_listener: Optional[EmailListener] = None


async def start_email_listener(broadcast_callback: Optional[Callable] = None):
    """Start the email listener background task."""
    global _listener

    if not settings.EMAIL_LISTENER_ENABLED:
        logger.info("Email listener is disabled")
        return

    _listener = EmailListener()

    if broadcast_callback:
        _listener.set_broadcast_callback(broadcast_callback)

    try:
        await _listener.run()
    except asyncio.CancelledError:
        logger.info("Email listener task cancelled")
    except Exception as e:
        logger.error(f"Email listener crashed: {e}")


async def stop_email_listener():
    """Stop the email listener background task."""
    global _listener
    if _listener:
        await _listener.stop()
