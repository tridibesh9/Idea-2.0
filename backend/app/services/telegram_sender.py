import os
import json
import uuid
from datetime import datetime
import httpx
import logging
from app.config import get_settings

logger = logging.getLogger("telegram_sender")

async def send_telegram_reply(chat_id: str, text: str) -> bool:
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        # Mock mode
        try:
            os.makedirs("mock_telegram/sent", exist_ok=True)
            filename = f"sent_{uuid.uuid4().hex[:8]}.json"
            filepath = os.path.join("mock_telegram/sent", filename)
            data = {
                "chat_id": chat_id,
                "text": text,
                "timestamp": datetime.utcnow().isoformat()
            }
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"[MOCK] Outgoing Telegram reply saved to {filepath} successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save mock Telegram reply: {e}")
            return False
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"chat_id": chat_id, "text": text})
        return response.status_code == 200
