import asyncio
from app.config import get_settings
from app.services.email_listener import EmailListener
import logging
from imap_tools import AND
#
logging.basicConfig(level=logging.INFO)

async def test():
    settings = get_settings()
    listener = EmailListener()
    print(f"Connecting to {listener.host}:{listener.port} as {listener.email}")
    mailbox = await listener.connect()
    print("Connected!")
    
    # fetch the last 2 messages regardless of seen status
    msgs = list(mailbox.fetch(limit=2, reverse=True))
    for msg in msgs:
        uid = msg.uid
        data = msg.obj.as_bytes()
        print(f"Processing UID: {uid}")
        try:
            complaint_id = await listener.process_email(data, uid)
            print(f"Processed into complaint_id: {complaint_id}")
        except Exception as e:
            print(f"Error processing UID {uid}: {e}")

asyncio.run(test())
