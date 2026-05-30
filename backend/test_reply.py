import asyncio
import uuid
import json
from datetime import datetime
from email.mime.text import MIMEText
from sqlalchemy import select
from app.config import get_settings
from app.database import async_session
from app.models.complaint import Complaint, ComplaintMessage
from app.services.email_listener import EmailListener

async def test():
    # 1. Create a dummy complaint
    async with async_session() as db:
        new_complaint = Complaint(
            id=uuid.uuid4(),
            channel="email",
            subject="My computer is broken",
            body="Help me",
            status="new",
        )
        db.add(new_complaint)
        await db.commit()
        complaint_id = str(new_complaint.id)
        print(f"Created complaint: {complaint_id}")

    # 2. Simulate an incoming reply email
    listener = EmailListener()
    
    reply_subject = f"Re: [Ticket #{complaint_id}] My computer is broken"
    msg = MIMEText("This is my follow up reply.")
    msg["Subject"] = reply_subject
    msg["From"] = "testuser@gmail.com"
    msg["Message-ID"] = "<reply123@gmail.com>"
    msg["Date"] = "Mon, 01 Jan 2026 12:00:00 +0000"
    
    raw_email_bytes = msg.as_bytes()
    
    # 3. Process the email
    processed_id = await listener.process_email(raw_email_bytes, "test_uid_1")
    print(f"Processed email, returned id: {processed_id}")
    
    # 4. Check the database
    async with async_session() as db:
        result = await db.execute(select(ComplaintMessage).where(ComplaintMessage.complaint_id == uuid.UUID(complaint_id)))
        messages = result.scalars().all()
        print(f"Messages for complaint {complaint_id}: {len(messages)}")
        for m in messages:
            print(f"- {m.content}")

asyncio.run(test())
