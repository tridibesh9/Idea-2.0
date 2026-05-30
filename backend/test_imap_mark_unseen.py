import asyncio
from app.config import get_settings
from app.services.email_listener import EmailListener
import logging
from imap_tools import AND

logging.basicConfig(level=logging.INFO)

async def test():
    settings = get_settings()
    listener = EmailListener()
    print(f"Connecting to {listener.host}:{listener.port} as {listener.email}")
    mailbox = await listener.connect()
    print("Connected!")
    
    # search for the last 2 messages and mark as unseen
    msgs = list(mailbox.fetch(limit=2, reverse=True))
    for msg in msgs:
        print(f"Marking UID {msg.uid} as unseen")
        mailbox.flag([msg.uid], "-FLAGS", "\\Seen")

asyncio.run(test())
