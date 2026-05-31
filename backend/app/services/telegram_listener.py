import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
import json
import uuid
import httpx

from sqlalchemy import select
from app.config import get_settings
from app.models.complaint import Complaint, ComplaintMessage, ComplaintEmbedding
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.models.entity import Entity
from app.services.classifier import classify_complaint
from app.services.duplicate_detector import generate_embedding
from app.services.pii_redactor import pii_redactor
from app.services.entity_extractor import extract_entities
from app.services.telegram_sender import send_telegram_reply
from app.database import async_session

logger = logging.getLogger("telegram_listener")
settings = get_settings()

SLA_HOURS = {"critical": 4, "high": 8, "medium": 24, "low": 72}

# In-memory state manager for Telegram users
# format: chat_id -> {"state": "IDLE" | "AWAITING_NEW" | "AWAITING_REPLY", "active_complaint_id": str | None}
user_states = {}

class TelegramListener:
    def __init__(self):
        self.is_running = False
        self._broadcast_callback: Optional[Callable] = None
        self.offset = 0

    def set_broadcast_callback(self, callback: Callable):
        self._broadcast_callback = callback

    def get_state(self, chat_id: str):
        return user_states.get(chat_id, {"state": "IDLE", "active_complaint_id": None})

    def set_state(self, chat_id: str, state: str, active_id: str = None):
        user_states[chat_id] = {"state": state, "active_complaint_id": active_id}

    async def send_menu(self, chat_id: str):
        markup = {
            "inline_keyboard": [
                [{"text": "📝 Submit a New Complaint", "callback_data": "cmd:new"}],
                [{"text": "📂 View Open Complaints", "callback_data": "cmd:list"}]
            ]
        }
        await send_telegram_reply(chat_id, "Welcome to Support! What would you like to do?", reply_markup=markup)

    async def process_update(self, update: dict) -> Optional[uuid.UUID]:
        try:
            if "callback_query" in update:
                cq = update["callback_query"]
                chat_id = str(cq["message"]["chat"]["id"])
                data = cq.get("data", "")
                
                # Acknowledge callback query
                if settings.TELEGRAM_BOT_TOKEN:
                    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
                    async with httpx.AsyncClient() as client:
                        await client.post(url, json={"callback_query_id": cq["id"]})

                if data == "cmd:new":
                    self.set_state(chat_id, "AWAITING_NEW")
                    await send_telegram_reply(chat_id, "Please type the details of your new complaint below:")
                    return None
                
                elif data == "cmd:list":
                    async with async_session() as db:
                        result = await db.execute(
                            select(Complaint)
                            .where(Complaint.external_id == chat_id, Complaint.status != "resolved", Complaint.status != "closed")
                            .order_by(Complaint.created_at.desc())
                            .limit(5)
                        )
                        complaints = result.scalars().all()
                        
                        if not complaints:
                            await send_telegram_reply(chat_id, "You don't have any open complaints.")
                            return None
                            
                        buttons = []
                        for c in complaints:
                            btn_text = f"🎫 {c.subject or c.category or 'Issue'} (ID: {str(c.id)[:8]})"
                            buttons.append([{"text": btn_text, "callback_data": f"resume:{str(c.id)}"}])
                            
                        markup = {"inline_keyboard": buttons}
                        await send_telegram_reply(chat_id, "Select a complaint to resume:", reply_markup=markup)
                    return None
                
                elif data.startswith("resume:"):
                    complaint_id_str = data.split(":")[1]
                    self.set_state(chat_id, "AWAITING_REPLY", complaint_id_str)
                    await send_telegram_reply(chat_id, f"You are now viewing ticket {complaint_id_str[:8]}. Any message you type now will be sent to the agent.")
                    return None

            if "message" not in update:
                return None
            
            message = update["message"]
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            if not text:
                return None
            
            if text in ["/start", "/menu"]:
                self.set_state(chat_id, "IDLE")
                await self.send_menu(chat_id)
                return None
            
            from_user = message.get("from", {})
            first_name = from_user.get("first_name", "Telegram User")
            
            customer_email = f"telegram_{chat_id}@telegram.local"
            user_state = self.get_state(chat_id)
            state_status = user_state["state"]
            active_id = user_state["active_complaint_id"]
            
            async with async_session() as db:
                result = await db.execute(select(Customer).where(Customer.email == customer_email))
                customer = result.scalar_one_or_none()
                
                if not customer:
                    customer = Customer(name=first_name, email=customer_email)
                    db.add(customer)
                    await db.flush()

                complaint = None
                if state_status == "AWAITING_REPLY" and active_id:
                    try:
                        c_id = uuid.UUID(active_id)
                        result = await db.execute(select(Complaint).where(Complaint.id == c_id))
                        complaint = result.scalar_one_or_none()
                    except ValueError:
                        pass

                if not complaint:
                    # New Complaint Workflow (or default if IDLE and typed a message)
                    safe_text, sensitive_entities_to_save = pii_redactor.redact(text)
                    business_entities_to_save = await extract_entities(safe_text)

                    complaint = Complaint(
                        channel="telegram",
                        external_id=chat_id,
                        subject=f"Telegram message from {first_name}",
                        body=text,
                        customer_id=customer.id,
                        status="new"
                    )
                    db.add(complaint)
                    await db.flush()

                    for token_type, tokens in sensitive_entities_to_save.items():
                        for val in tokens:
                            db.add(Entity(complaint_id=complaint.id, entity_type=token_type, entity_value=val, is_sensitive=True))
                    for be in business_entities_to_save:
                        db.add(Entity(complaint_id=complaint.id, entity_type=be.get("entity_type"), entity_value=be.get("entity_value"), is_sensitive=False))

                    # AI Classification
                    classification = await classify_complaint(text, "telegram")
                    complaint.category = classification.category
                    complaint.product = classification.product
                    complaint.severity = classification.severity
                    complaint.sentiment_score = classification.sentiment_score
                    complaint.sentiment_label = classification.sentiment_label
                    complaint.key_issues = json.dumps(classification.key_issues)
                    complaint.ai_confidence_score = classification.confidence
                    complaint.regulatory_flags = json.dumps(classification.regulatory_flags)
                    if classification.subject:
                        complaint.subject = classification.subject

                    hours = SLA_HOURS.get(classification.severity, 24)
                    complaint.sla_deadline = datetime.now(timezone.utc) + timedelta(hours=hours)

                    # Smart Routing Auto Assignment
                    from app.services.smart_router import route_complaint
                    await route_complaint(complaint, db)

                    # Generate embedding
                    try:
                        embedding_vector = await generate_embedding(text)
                        if embedding_vector:
                            emb = ComplaintEmbedding(complaint_id=complaint.id, embedding=embedding_vector)
                            db.add(emb)
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding: {e}")

                    audit = AuditLog(
                        complaint_id=complaint.id,
                        action="telegram_received",
                        performed_by="system",
                        details=json.dumps({"chat_id": chat_id, "classification": classification.model_dump()})
                    )
                    db.add(audit)
                    
                    # Lock user to this new ticket
                    self.set_state(chat_id, "AWAITING_REPLY", str(complaint.id))
                    await send_telegram_reply(chat_id, f"Your complaint has been submitted! Ticket ID: {str(complaint.id)[:8]}. We will get back to you shortly.")
                    
                else:
                    # Resumed/Active Workflow
                    complaint.updated_at = datetime.now(timezone.utc)
                    if complaint.status != "new":
                        complaint.status = "open"

                msg = ComplaintMessage(
                    complaint_id=complaint.id,
                    sender_type="customer",
                    sender_name=first_name,
                    content=text,
                    channel="telegram",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(msg)

                audit = AuditLog(
                    complaint_id=complaint.id,
                    action="telegram_message_added",
                    performed_by="system",
                    details=json.dumps({"chat_id": chat_id})
                )
                db.add(audit)

                await db.commit()

                if self._broadcast_callback:
                    try:
                        await self._broadcast_callback({
                            "type": "new_complaint",
                            "complaint_id": str(complaint.id),
                            "subject": complaint.subject,
                            "category": complaint.category,
                            "severity": complaint.severity,
                            "customer": first_name,
                            "channel": "telegram",
                        })
                    except Exception as e:
                        logger.warning(f"Failed to broadcast: {e}")

                return complaint.id

        except Exception as e:
            logger.error(f"Error processing telegram update: {e}")
            return None

    async def run(self):
        is_mock_mode = not settings.TELEGRAM_BOT_TOKEN

        self.is_running = True

        if is_mock_mode:
            logger.info("Telegram listener running in MOCK mode (monitoring mock_telegram/inbox directory)")
            import os
            os.makedirs("mock_telegram/inbox", exist_ok=True)
            os.makedirs("mock_telegram/sent", exist_ok=True)

            while self.is_running:
                try:
                    inbox_dir = "mock_telegram/inbox"
                    if os.path.exists(inbox_dir):
                        files = os.listdir(inbox_dir)
                        for filename in files:
                            if not self.is_running:
                                break
                            filepath = os.path.join(inbox_dir, filename)
                            if os.path.isfile(filepath) and filename.endswith(".json"):
                                try:
                                    logger.info(f"Mock Telegram listener found file: {filename}")
                                    with open(filepath, "r") as f:
                                        update = json.load(f)
                                    await self.process_update(update)
                                    os.remove(filepath)
                                    logger.info(f"Processed and removed mock Telegram message: {filename}")
                                except Exception as e:
                                    logger.error(f"Error processing mock Telegram file {filename}: {e}")
                    await asyncio.sleep(settings.TELEGRAM_CHECK_INTERVAL)
                except Exception as e:
                    logger.error(f"Mock Telegram listener error: {e}")
                    await asyncio.sleep(5)
        else:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"
            async with httpx.AsyncClient(timeout=30.0) as client:
                while self.is_running:
                    try:
                        response = await client.get(url, params={"offset": self.offset, "timeout": 20})
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("ok"):
                                for update in data.get("result", []):
                                    update_id = update["update_id"]
                                    self.offset = update_id + 1
                                    await self.process_update(update)
                        
                        await asyncio.sleep(settings.TELEGRAM_CHECK_INTERVAL)
                    except Exception as e:
                        logger.error(f"Telegram listener error: {e}")
                        await asyncio.sleep(5)

    async def stop(self):
        self.is_running = False
        logger.info("Telegram listener stopped")

_telegram_listener: Optional[TelegramListener] = None

async def start_telegram_listener(broadcast_callback: Optional[Callable] = None):
    global _telegram_listener
    if not settings.TELEGRAM_LISTENER_ENABLED:
        return
    
    _telegram_listener = TelegramListener()
    if broadcast_callback:
        _telegram_listener.set_broadcast_callback(broadcast_callback)
    
    try:
        await _telegram_listener.run()
    except asyncio.CancelledError:
        logger.info("Telegram listener task cancelled")
    except Exception as e:
        logger.error(f"Telegram listener crashed: {e}")

async def stop_telegram_listener():
    global _telegram_listener
    if _telegram_listener:
        await _telegram_listener.stop()
