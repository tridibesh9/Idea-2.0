import asyncio
from app.config import get_settings
from app.services.email_listener import EmailListener
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    settings = get_settings()
    listener = EmailListener()
    print(f"Connecting to {listener.host}:{listener.port} as {listener.email}")
    mailbox = await listener.connect()
    print("Connected!")
    emails = await listener.fetch_unseen_emails(mailbox)
    print(f"Found {len(emails)} unseen emails")
    for uid, data in emails:
        print(f"Processing UID: {uid}")
        try:
            complaint_id = await listener.process_email(data, uid)
            print(f"Processed into complaint_id: {complaint_id}")
            if complaint_id:
                # Optionally mark as seen if processed successfully for testing
                # await listener.mark_as_seen(mailbox, uid)
                pass
        except Exception as e:
            print(f"Error processing: {e}")

asyncio.run(test())
