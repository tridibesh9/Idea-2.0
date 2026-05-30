import asyncio
from app.config import get_settings
from app.services.email_listener import EmailListener
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    settings = get_settings()
    listener = EmailListener()
    mailbox = await listener.connect()
    try:
        mailbox.flag(["5"], "+FLAGS", "\\Seen", silent=True)
        print("Success with original code")
    except Exception as e:
        print(f"Error with original code: {e}")
        
    try:
        from imap_tools import MailMessageFlags
        mailbox.flag(["5"], MailMessageFlags.SEEN, True)
        print("Success with correct code")
    except Exception as e:
        print(f"Error with correct code: {e}")

asyncio.run(test())
