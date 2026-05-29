import httpx
from app.config import get_settings

async def send_telegram_reply(chat_id: str, text: str, reply_markup: dict = None) -> bool:
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        return response.status_code == 200
