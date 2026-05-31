import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.schemas import ComplaintCreate, ComplaintResponse
from app.routes.complaints import create_complaint
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# ── Realistic templates per channel ──

EMAIL_TEMPLATES = [
    {"subject": "Urgent: Unauthorized transactions on my account", "body": "Dear Support,\n\nI have noticed three unauthorized transactions on my credit card ending in 4532 from March 5-7. The charges total $847.50 from merchants I don't recognize. I have not shared my card details with anyone. Please investigate immediately and reverse these charges.\n\nI'm extremely worried about the security of my account. If this isn't resolved within 24 hours, I will be contacting the financial ombudsman.\n\nRegards,\nSarah Chen"},
    {"subject": "Billing discrepancy - charged twice for monthly premium", "body": "Hello,\n\nI was charged twice for my monthly insurance premium this month — once on Mar 1 ($189.00) and again on Mar 3 ($189.00). My policy number is INS-2024-78432. This is the second time this has happened in the last quarter.\n\nPlease refund the duplicate charge immediately. I've attached my bank statement showing both deductions.\n\nThank you,\nMichael Rodriguez"},
    {"subject": "Cannot access my online banking for 3 days", "body": "Hi there,\n\nI've been locked out of my online banking since Friday. I've tried resetting my password multiple times but keep getting 'System Error 503'. I called the helpline on Saturday and was on hold for 45 minutes before giving up. I need to make an urgent payment by tomorrow.\n\nThis level of service is unacceptable for a premium account holder. Please escalate this.\n\nBest,\nJames Patterson"},
    {"subject": "Refund not received after product return 30 days ago", "body": "Dear Customer Service,\n\nI returned a defective laptop (Order #ORD-2024-11583) on February 10th. Your return policy states refunds are processed within 7-10 business days. It has now been 30 days and I still haven't received my $1,299.99 refund.\n\nI have the return shipping receipt and tracking confirmation. Please process this immediately.\n\nFrustrated customer,\nEmily Watson"},
]

TWITTER_TEMPLATES = [
    {"subject": "@CompanyHelp your app is down AGAIN", "body": "@CompanyHelp Your mobile app has been crashing non-stop since the last update. Can't check my balance, can't transfer money. This is the 3rd time this month! Fix your app or I'm switching to a competitor. #worst_service #appdown"},
    {"subject": "@CompanyHelp still waiting for my refund!!!", "body": "@CompanyHelp It's been 3 WEEKS since I was promised a refund for the wrong item sent. Case #CS-8832. Every time I call, I get transferred to someone new who has no idea about my case. This is ridiculous! #customerservice #fail"},
    {"subject": "@CompanyHelp hidden fees on my statement", "body": "@CompanyHelp Can someone explain why I'm being charged a $35 'account maintenance fee' that was NEVER disclosed when I signed up? This feels like fraud. I want this reversed immediately and an explanation. #hiddenfees #scam"},
    {"subject": "@CompanyHelp delivery 2 weeks late", "body": "@CompanyHelp Ordered express delivery (paid extra $25!) and it's been 14 days. Tracking says 'in transit' for a week. No one answers your phone line. I need this for a gift TOMORROW. Terrible service. #neveragain"},
]

CHAT_TEMPLATES = [
    {"subject": "Live Chat: Card declined at store", "body": "Hi, I'm at the grocery store right now and my debit card was just declined. I have over $5,000 in my checking account. This is really embarrassing. Can you tell me why my card isn't working? I need to buy groceries for my family."},
    {"subject": "Live Chat: Need to dispute a charge", "body": "I see a charge of $499.99 from 'ELECTROMAX ONLINE' on my statement from yesterday. I never made this purchase. I think my card was compromised. Can you block my card immediately and start a dispute? I'm very concerned."},
    {"subject": "Live Chat: Account statement error", "body": "Hello, my March statement shows a closing balance of $2,340 but my online banking shows $3,890. There's a $1,550 difference. Which one is correct? I need this sorted out because I'm filing my taxes this week."},
    {"subject": "Live Chat: Loan application stuck", "body": "I applied for a personal loan 2 weeks ago (App #LA-2024-5567) and haven't heard anything back. I was told it would take 3-5 business days. I've emailed twice with no response. Can someone check the status? I really need this loan for a medical emergency."},
]

PHONE_TEMPLATES = [
    {"subject": "Phone Call Transcript: Insurance claim delay", "body": "[PHONE TRANSCRIPT]\nCaller: I filed a home insurance claim 6 weeks ago after the storm damage to my roof. Claim number IC-2024-3321. The adjuster came out 4 weeks ago and I haven't heard a single thing since. Every time I call, I'm told 'it's being processed.' My roof is literally leaking and causing more damage every day.\nSentiment: Very frustrated, raised voice\nPriority note: Property damage worsening"},
    {"subject": "Phone Call Transcript: Mortgage rate complaint", "body": "[PHONE TRANSCRIPT]\nCaller: I was promised a 5.2% mortgage rate when I signed up in January. Now I see my payment has gone up and the rate is 5.8%. Nobody told me about this change. My loan officer, David Chang, specifically said the rate was locked for 12 months. I want this corrected or I'm contacting my lawyer and the banking regulator.\nSentiment: Angry, mentioned legal action\nPriority note: Regulatory escalation risk"},
    {"subject": "Phone Call Transcript: Wire transfer missing", "body": "[PHONE TRANSCRIPT]\nCaller: I sent a $15,000 wire transfer to my daughter's college on March 1st. It's March 10th and the school says they never received it. The money was deducted from my account immediately. Where is my money? This was for tuition due by March 15th. I need this resolved TODAY.\nSentiment: Panicked, high urgency\nPriority note: Large sum, time-sensitive"},
    {"subject": "Phone Call Transcript: Service downgrade without consent", "body": "[PHONE TRANSCRIPT]\nCaller: I just found out my premium business account was downgraded to a basic account. I was never notified and I didn't authorize this. I've lost access to all premium features including priority support and higher transfer limits. I have a $50,000 transfer that was rejected because of this. Who authorized this change to my account?\nSentiment: Irate, demanding escalation\nPriority note: Unauthorized account change, high-value customer"},
]

CUSTOMER_NAMES = [
    ("Sarah Chen", "sarah.chen@email.com"),
    ("Michael Rodriguez", "michael.r@email.com"),
    ("James Patterson", "james.patterson@email.com"),
    ("Emily Watson", "emily.w@email.com"),
    ("Priya Sharma", "priya.sharma@email.com"),
    ("David Kim", "d.kim@email.com"),
    ("Lisa Thompson", "l.thompson@email.com"),
    ("Robert Martinez", "r.martinez@email.com"),
    ("Anna Kowalski", "a.kowalski@email.com"),
    ("Chris Johnson", "chris.j@email.com"),
]


def _pick_template(channel: str) -> dict:
    templates = {
        "email": EMAIL_TEMPLATES,
        "twitter": TWITTER_TEMPLATES,
        "chat": CHAT_TEMPLATES,
        "phone": PHONE_TEMPLATES,
    }
    pool = templates.get(channel, EMAIL_TEMPLATES)
    return random.choice(pool)


@router.post("/simulate/{channel}", response_model=ComplaintResponse, status_code=201)
async def simulate_channel_intake(channel: str, db: AsyncSession = Depends(get_db)):
    """Simulate a complaint arriving via a specific channel."""
    if channel not in ("email", "twitter", "chat", "phone"):
        channel = "email"

    template = _pick_template(channel)
    name, email = random.choice(CUSTOMER_NAMES)

    # If channel is email and email listener is enabled, run raw EML mock simulation to test email listener!
    if channel == "email" and settings.EMAIL_LISTENER_ENABLED:
        is_mock_mode = (settings.IMAP_HOST == "localhost") or (not settings.IMAP_EMAIL or not settings.IMAP_PASSWORD)
        if is_mock_mode:
            import os
            import uuid
            import asyncio
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from sqlalchemy import select
            from app.models.complaint import Complaint

            # Construct raw EML
            msg = MIMEMultipart()
            msg["From"] = f"{name} <{email}>"
            msg["To"] = settings.SUPPORT_EMAIL
            msg["Subject"] = template["subject"]
            msg["Message-ID"] = f"<{uuid.uuid4()}@client.example.com>"
            msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
            msg.attach(MIMEText(template["body"], "plain", "utf-8"))

            os.makedirs("mock_emails/inbox", exist_ok=True)
            filename = f"incoming_{uuid.uuid4().hex[:8]}.eml"
            filepath = os.path.join("mock_emails/inbox", filename)
            with open(filepath, "wb") as f:
                f.write(msg.as_bytes())

            # Poll database to wait for background listener to process and create it
            for _ in range(30):  # Wait up to 3 seconds
                await asyncio.sleep(0.1)
                result = await db.execute(
                    select(Complaint).where(Complaint.external_id == msg["Message-ID"])
                )
                complaint = result.scalar_one_or_none()
                if complaint:
                    return complaint

    payload = ComplaintCreate(
        channel=channel,
        subject=template["subject"],
        body=template["body"],
        customer_name=name,
        customer_email=email,
    )

    complaint = await create_complaint(payload, db)
    return complaint


@router.post("/simulate/burst", status_code=201)
async def simulate_burst(count: int = 5, db: AsyncSession = Depends(get_db)):
    """Simulate a burst of complaints across random channels for demo purposes."""
    if count > 20:
        count = 20
    channels = ["email", "twitter", "chat", "phone"]
    results = []
    for _ in range(count):
        ch = random.choice(channels)
        template = _pick_template(ch)
        name, email = random.choice(CUSTOMER_NAMES)
        payload = ComplaintCreate(
            channel=ch,
            subject=template["subject"],
            body=template["body"],
            customer_name=name,
            customer_email=email,
        )
        complaint = await create_complaint(payload, db)
        results.append({
            "id": str(complaint.id),
            "channel": ch,
            "severity": complaint.severity,
            "category": complaint.category,
        })

    return {"simulated": len(results), "complaints": results}


from pydantic import BaseModel
import os
import json
import uuid
import glob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class IncomingTelegramMock(BaseModel):
    chat_id: str
    first_name: str
    text: str

class IncomingEmailMock(BaseModel):
    from_email: str
    from_name: str
    subject: str
    body: str

@router.post("/telegram/incoming")
async def simulate_incoming_telegram(payload: IncomingTelegramMock):
    """Write an incoming mock Telegram update JSON to trigger the listener."""
    import random
    os.makedirs("mock_telegram/inbox", exist_ok=True)
    update = {
        "update_id": random.randint(100000, 999999),
        "message": {
            "message_id": random.randint(1, 10000),
            "chat": {
                "id": int(payload.chat_id) if payload.chat_id.isdigit() else 123456
            },
            "from": {
                "first_name": payload.first_name,
                "is_bot": False
            },
            "text": payload.text,
            "date": int(datetime.now(timezone.utc).timestamp())
        }
    }
    filename = f"incoming_{uuid.uuid4().hex[:8]}.json"
    filepath = os.path.join("mock_telegram/inbox", filename)
    with open(filepath, "w") as f:
        json.dump(update, f, indent=2)
    return {"success": True, "file": filename}


@router.post("/email/incoming")
async def simulate_incoming_email(payload: IncomingEmailMock):
    """Write an incoming mock Email EML to trigger the listener."""
    os.makedirs("mock_emails/inbox", exist_ok=True)
    msg = MIMEMultipart()
    msg["From"] = f"{payload.from_name} <{payload.from_email}>"
    msg["To"] = settings.SUPPORT_EMAIL
    msg["Subject"] = payload.subject
    msg["Message-ID"] = f"<{uuid.uuid4()}@client.example.com>"
    msg["Date"] = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg.attach(MIMEText(payload.body, "plain", "utf-8"))

    filename = f"incoming_{uuid.uuid4().hex[:8]}.eml"
    filepath = os.path.join("mock_emails/inbox", filename)
    with open(filepath, "wb") as f:
        f.write(msg.as_bytes())
    return {"success": True, "file": filename}


@router.get("/sent-messages")
async def get_sent_messages():
    """Retrieve all logged mock outgoing email and Telegram messages."""
    import email
    import glob
    
    emails = []
    telegram = []

    # Parse sent emails
    email_dir = "mock_emails/sent"
    if os.path.exists(email_dir):
        for filepath in glob.glob(os.path.join(email_dir, "*.eml")):
            try:
                with open(filepath, "rb") as f:
                    msg = email.message_from_bytes(f.read())
                
                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

                emails.append({
                    "id": os.path.basename(filepath),
                    "recipient": msg.get("To", "unknown"),
                    "subject": msg.get("Subject", "No Subject"),
                    "body": body,
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
            except Exception as e:
                print(f"Error parsing sent EML: {e}")

    # Parse sent telegrams
    tg_dir = "mock_telegram/sent"
    if os.path.exists(tg_dir):
        for filepath in glob.glob(os.path.join(tg_dir, "*.json")):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                telegram.append({
                    "id": os.path.basename(filepath),
                    "chat_id": data.get("chat_id"),
                    "text": data.get("text"),
                    "timestamp": data.get("timestamp")
                })
            except Exception as e:
                print(f"Error parsing sent Telegram json: {e}")

    # Sort by timestamp descending
    emails.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    telegram.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {"emails": emails, "telegram": telegram}
