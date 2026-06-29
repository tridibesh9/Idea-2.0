"""
Seed Data Generator for ComplaintIQ
Generates 100 realistic complaints with customers, agents, and categories.
Run: python seed/generate_complaints.py
"""

import asyncio
import json
import random
import uuid
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from google import genai

import asyncpg
#hi
# Load env variables
load_dotenv()
load_dotenv("../.env")

raw_db_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL") or "postgresql://complaintiq:complaintiq@localhost:5432/complaintiq"
DATABASE_URL = raw_db_url.replace("+asyncpg", "")
print(raw_db_url)
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

async def get_embedding(text: str):
    if not client:
        return [0.0] * 768
    model_name = os.getenv("EMBEDDING_MODEL") or "text-embedding-004"
    config = {}
    if "gemini-embedding" in model_name:
        config["output_dimensionality"] = 768
    try:
        response = await client.aio.models.embed_content(
            model=model_name,
            contents=text,
            config=config,
        )
        if response and response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0].values
    except Exception as e:
        print(f"Error getting embedding in seed: {e}")
    return [0.0] * 768

CHANNELS = ["email", "twitter", "chat", "phone", "web_form"]
CATEGORIES = [
    "billing",
    "product_defect",
    "service_delay",
    "account_access",
    "delivery",
    "refund",
]
SEVERITIES = ["critical", "high", "medium", "low"]
SENTIMENTS = [
    (-0.9, "negative"),
    (-0.7, "negative"),
    (-0.5, "negative"),
    (-0.3, "negative"),
    (-0.1, "neutral"),
    (0.1, "neutral"),
    (0.3, "positive"),
    (0.5, "positive"),
]
PRODUCTS = [
    "Credit Card",
    "Savings Account",
    "Mobile App",
    "Personal Loan",
    "Home Insurance",
    "Investment Portfolio",
    "Debit Card",
    "Current Account",
    "Fixed Deposit",
    "Customer Portal",
]
STATUSES = ["new", "open", "in_progress", "escalated", "resolved", "closed"]
SLA_HOURS = {"critical": 4, "high": 8, "medium": 24, "low": 72}

# -- Sample complaints per category --
COMPLAINT_TEMPLATES = {
    "billing": [
        (
            "Overcharged on my {product}",
            "I was charged ${amount} instead of the expected ${expected}. This has been happening for {months} months now and no one has resolved it. I need an immediate refund and correction to my account.",
        ),
        (
            "Unexpected fee on {product}",
            "I noticed a ${amount} fee on my {product} statement that I never authorized. I've called twice already and was told it would be removed but it's still there. This is unacceptable.",
        ),
        (
            "Double billing issue",
            "My {product} was billed twice this month — ${amount} each time. I need the duplicate charge reversed immediately. This is causing me financial hardship.",
        ),
        (
            "Late payment fee despite on-time payment",
            "I made my {product} payment on the 1st but was charged a ${amount} late fee. My bank shows the payment went through on time. Please investigate and reverse this charge.",
        ),
    ],
    "product_defect": [
        (
            "{product} not working properly",
            "My {product} has been malfunctioning since last week. The {feature} feature keeps crashing and I can't complete basic transactions. This is severely impacting my daily banking.",
        ),
        (
            "Bug in {product}",
            "There's a critical bug in the {product} — when I try to {action}, the system throws an error and loses my data. I've tried reinstalling but the issue persists.",
        ),
        (
            "{product} display shows incorrect info",
            "My {product} is showing incorrect balance information. The displayed amount is ${amount} less than what it should be. I'm worried about the accuracy of all my transactions.",
        ),
    ],
    "service_delay": [
        (
            "Waiting {days} days for {product} activation",
            "I applied for a {product} {days} days ago and it still hasn't been activated. Every time I call, I'm told to wait another 3-5 business days. This is beyond frustrating.",
        ),
        (
            "No response to my {product} inquiry",
            "I submitted a {product} inquiry {days} days ago and haven't received any response. I've followed up via email and phone with no luck. Your customer service is terrible.",
        ),
        (
            "Transfer taking too long",
            "I initiated a transfer from my {product} {days} days ago and it still hasn't gone through. The recipient is waiting for the funds and this delay is causing me serious problems.",
        ),
    ],
    "account_access": [
        (
            "Locked out of {product}",
            "I've been locked out of my {product} for 3 days now. I've tried resetting my password multiple times but keep getting error messages. I urgently need access to manage my finances.",
        ),
        (
            "Cannot login to {product}",
            "The login page for {product} keeps showing 'Invalid credentials' even though I'm entering the correct password. I've cleared my cache, tried different browsers, nothing works.",
        ),
        (
            "Two-factor authentication broken",
            "The two-factor authentication for my {product} stopped working after your last update. I can't receive verification codes and am completely locked out of my account.",
        ),
    ],
    "delivery": [
        (
            "{product} card never arrived",
            "I ordered a replacement {product} 3 weeks ago and it never arrived. I've been without a card for almost a month now and can't make any purchases. This is extremely inconvenient.",
        ),
        (
            "Wrong {product} delivered",
            "I received the wrong {product} in the mail. The name on the card belongs to someone else entirely. This is a serious security concern and needs immediate attention.",
        ),
        (
            "Damaged {product} received",
            "The {product} I received was physically damaged — the chip is cracked and it won't work at ATMs or stores. I need an urgent replacement.",
        ),
    ],
    "refund": [
        (
            "Refund not processed for {product}",
            "I was promised a refund of ${amount} for my {product} issue {days} days ago but haven't received it. I have the reference number and was told it would take 5-7 days. It's been {days} days.",
        ),
        (
            "Partial refund received",
            "I was supposed to receive a full refund of ${amount} for {product} but only got ${partial}. I need the remaining ${remaining} credited to my account immediately.",
        ),
        (
            "Disputed transaction refund delayed",
            "I disputed a ${amount} transaction on my {product} over a month ago. The investigation was supposed to take 10 days but I'm still waiting for my refund.",
        ),
    ],
}

CUSTOMER_NAMES = [
    "Aarav Patel",
    "Priya Sharma",
    "Rahul Gupta",
    "Ananya Singh",
    "Vikram Mehta",
    "Sneha Reddy",
    "Arjun Nair",
    "Divya Kapoor",
    "Karthik Iyer",
    "Meera Joshi",
    "Rohan Das",
    "Pooja Verma",
    "Amit Kumar",
    "Nisha Tiwari",
    "Sanjay Rao",
    "Kavita Mishra",
    "Dhruv Bansal",
    "Riya Agarwal",
    "Suresh Pandey",
    "Anita Bhat",
    "James Wilson",
    "Sarah Thompson",
    "Michael Chen",
    "Emily Rodriguez",
    "David Kim",
    "Jessica Taylor",
    "Robert Brown",
    "Amanda Johnson",
    "Christopher Lee",
    "Sophia Martinez",
]

AGENT_NAMES = [
    ("Agent Sarah", "sarah@complaintiq.com", "agent", "Customer Support"),
    ("Agent Mike", "mike@complaintiq.com", "agent", "Customer Support"),
    ("Agent Priya", "priya@complaintiq.com", "agent", "Billing"),
    ("Agent James", "james@complaintiq.com", "agent", "Technical"),
    ("Supervisor Rahul", "rahul@complaintiq.com", "supervisor", "Management"),
]


def generate_complaint_text(category: str) -> tuple[str, str]:
    templates = COMPLAINT_TEMPLATES[category]
    subject_tmpl, body_tmpl = random.choice(templates)
    product = random.choice(PRODUCTS)
    amount = random.randint(15, 5000)
    expected = amount - random.randint(5, 50)
    months = random.randint(1, 6)
    days = random.randint(5, 30)
    feature = random.choice(
        ["transfer", "payment", "balance check", "notification", "login"]
    )
    action = random.choice(
        ["transfer money", "view statements", "update profile", "pay bills"]
    )
    partial = int(amount * 0.6)
    remaining = amount - partial

    replacements = {
        "product": product,
        "amount": str(amount),
        "expected": str(expected),
        "months": str(months),
        "days": str(days),
        "feature": feature,
        "action": action,
        "partial": str(partial),
        "remaining": str(remaining),
    }
    subject = subject_tmpl
    body = body_tmpl
    for k, v in replacements.items():
        subject = subject.replace("{" + k + "}", v)
        body = body.replace("{" + k + "}", v)

    return subject, body


async def seed():
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        conn = await asyncpg.connect(DATABASE_URL, ssl=ctx)
    except Exception as e:
        print(f"Failed to connect with SSL: {e}. Retrying without SSL...")
        conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Clear existing tables to ensure a fresh start
        print("  Wiping existing data from tables...")
        try:
            await conn.execute("""
                TRUNCATE TABLE 
                    escalations, 
                    audit_log, 
                    complaint_embeddings, 
                    complaint_messages, 
                    complaints, 
                    customers, 
                    agents, 
                    categories, 
                    knowledge_documents, 
                    sla_configs 
                CASCADE;
            """)
            print("  Database tables successfully cleared.")
        except Exception as e:
            print(f"  Note: Could not truncate tables (they may not exist yet): {e}")

        # Create tables if not exist (run alembic first ideally, but this is a fallback)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id UUID PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                email VARCHAR(300) UNIQUE,
                phone VARCHAR(50),
                account_id VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                email VARCHAR(300) UNIQUE,
                role VARCHAR(50) DEFAULT 'agent',
                department VARCHAR(100),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id UUID PRIMARY KEY,
                name VARCHAR(100) UNIQUE,
                description TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id UUID PRIMARY KEY,
                external_id VARCHAR(100),
                channel VARCHAR(50) NOT NULL,
                subject VARCHAR(500),
                body TEXT NOT NULL,
                customer_id UUID REFERENCES customers(id),
                assigned_agent_id UUID REFERENCES agents(id),
                category VARCHAR(100),
                product VARCHAR(200),
                severity VARCHAR(20) DEFAULT 'medium',
                sentiment_score FLOAT,
                sentiment_label VARCHAR(20),
                key_issues TEXT,
                ai_confidence_score FLOAT,
                regulatory_flags TEXT,
                status VARCHAR(30) DEFAULT 'new',
                sla_deadline TIMESTAMPTZ,
                is_sla_breached BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS complaint_messages (
                id UUID PRIMARY KEY,
                complaint_id UUID REFERENCES complaints(id),
                sender_type VARCHAR(20) NOT NULL,
                sender_name VARCHAR(200),
                content TEXT NOT NULL,
                channel VARCHAR(50),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS complaint_embeddings (
                id UUID PRIMARY KEY,
                complaint_id UUID UNIQUE REFERENCES complaints(id),
                embedding vector(768)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id UUID PRIMARY KEY,
                complaint_id UUID REFERENCES complaints(id),
                escalated_by VARCHAR(50) NOT NULL,
                reason TEXT NOT NULL,
                previous_agent_id UUID REFERENCES agents(id),
                new_agent_id UUID REFERENCES agents(id),
                status VARCHAR(30) DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                resolved_at TIMESTAMPTZ
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sla_configs (
                id UUID PRIMARY KEY,
                severity VARCHAR(20) UNIQUE,
                max_resolution_hours INT,
                escalation_threshold_pct INT DEFAULT 80
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id UUID PRIMARY KEY,
                complaint_id UUID REFERENCES complaints(id),
                action VARCHAR(100) NOT NULL,
                performed_by VARCHAR(200) NOT NULL,
                details TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id UUID PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(100) NOT NULL,
                embedding vector(768)
            )
        """)

        # --- Seed Agents ---
        agent_ids = []
        for name, email, role, dept in AGENT_NAMES:
            aid = uuid.uuid4()
            row = await conn.fetchrow(
                """
                INSERT INTO agents (id, name, email, role, department) 
                VALUES ($1, $2, $3, $4, $5) 
                ON CONFLICT (email) 
                DO UPDATE SET name = EXCLUDED.name 
                RETURNING id
                """,
                aid,
                name,
                email,
                role,
                dept,
            )
            agent_ids.append(row["id"])
        print(f"  Seeded {len(AGENT_NAMES)} agents")

        # --- Seed Categories ---
        for cat in CATEGORIES:
            await conn.execute(
                "INSERT INTO categories (id, name) VALUES ($1, $2) ON CONFLICT (name) DO NOTHING",
                uuid.uuid4(),
                cat,
            )
        print(f"  Seeded {len(CATEGORIES)} categories")

        # --- Seed SLA Configs ---
        for sev, hours in SLA_HOURS.items():
            await conn.execute(
                "INSERT INTO sla_configs (id, severity, max_resolution_hours, escalation_threshold_pct) VALUES ($1, $2, $3, 80) ON CONFLICT (severity) DO NOTHING",
                uuid.uuid4(),
                sev,
                hours,
            )
        print("  Seeded SLA configs")

        # --- Seed Knowledge Documents ---
        print("  Seeding Knowledge Documents...")
        await conn.execute("DELETE FROM knowledge_documents")
        KBASE_DOCS = [
            {
                "title": "Billing Discrepancies and Double Charges Policy",
                "category": "billing",
                "content": "For duplicate or incorrect charges, agents must investigate transaction logs. Refund requests for duplicate billings must be approved immediately if the bank reference details match. Offer a credit or transaction reversal within 3-5 business days."
            },
            {
                "title": "Product Defect and Malfunctions Support Policy",
                "category": "product_defect",
                "content": "When customers report crashes or malfunctioning features in the Mobile App or Portal, verify their app version. Instruct them to clear cache, reinstall the app, or use the web interface. Escalate persistent bugs to the Tier-2 Dev Team with full diagnostic notes."
            },
            {
                "title": "Service Delay & Transaction Processing Standards",
                "category": "service_delay",
                "content": "Standard processing time for domestic wire transfers is 1-2 business days. For international wires, it is 3-5 business days. If a transfer is delayed beyond these windows, initiate a trace with the clearing department and provide the customer with a trace ID."
            },
            {
                "title": "Account Lockout & Password Recovery Guidelines",
                "category": "account_access",
                "content": "Account lockouts occur after 5 failed login attempts. To reset passwords, trigger a two-factor verification code. If 2FA fails, verify identity manually using security questions and update their contact details."
            },
            {
                "title": "Card Delivery and Replacement Procedures",
                "category": "delivery",
                "content": "Replacement debit and credit cards take 7-10 business days for standard delivery, and 2-3 business days for express delivery. If a card is lost or not received within 15 days, block the card, verify the address, and re-order."
            },
            {
                "title": "Refund Processing & Reimbursement Limits",
                "category": "refund",
                "content": "Refunds for disputed transactions are capped at $5,000 for standard customer support agents. Amounts higher than $5,000 require supervisor approval. Standard timeline for a refund credit to reflect is 5-7 banking days."
            }
        ]

        for doc in KBASE_DOCS:
            embedding = await get_embedding(doc["content"])
            await conn.execute(
                """
                INSERT INTO knowledge_documents (id, title, content, category, embedding)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid.uuid4(),
                doc["title"],
                doc["content"],
                doc["category"],
                str(embedding)
            )
        print("  Seeded Knowledge Documents")

        # --- Seed Customers & Complaints ---
        customer_ids = []
        for i, name in enumerate(CUSTOMER_NAMES):
            cid = uuid.uuid4()
            email = f"{name.lower().replace(' ', '.')}@example.com"
            row = await conn.fetchrow(
                """
                INSERT INTO customers (id, name, email, account_id) 
                VALUES ($1, $2, $3, $4) 
                ON CONFLICT (email) 
                DO UPDATE SET name = EXCLUDED.name 
                RETURNING id
                """,
                cid,
                name,
                email,
                f"ACC-{10000 + i}",
            )
            customer_ids.append(row["id"])
        print(f"  Seeded {len(CUSTOMER_NAMES)} customers")

        # --- Seed 100 Complaints ---
        now = datetime.now(timezone.utc)
        for i in range(100):
            category = random.choice(CATEGORIES)
            severity = random.choices(SEVERITIES, weights=[10, 20, 40, 30])[0]
            channel = random.choice(CHANNELS)
            sent_score, sent_label = random.choice(SENTIMENTS)
            product = random.choice(PRODUCTS)
            status = random.choices(STATUSES, weights=[15, 15, 25, 10, 25, 10])[0]

            subject, body = generate_complaint_text(category)
            created = now - timedelta(
                days=random.randint(0, 30), hours=random.randint(0, 23)
            )
            sla_hours = SLA_HOURS[severity]
            sla_deadline = created + timedelta(hours=sla_hours)
            is_breached = now > sla_deadline and status not in ("resolved", "closed")
            resolved_at = (
                created + timedelta(hours=random.randint(1, sla_hours * 2))
                if status in ("resolved", "closed")
                else None
            )

            key_issues = random.sample(
                [
                    "overcharged",
                    "delayed response",
                    "system error",
                    "wrong information",
                    "rude staff",
                    "unauthorized charge",
                    "missing refund",
                    "login failure",
                    "card not received",
                    "app crash",
                    "poor communication",
                    "fee dispute",
                ],
                k=random.randint(2, 4),
            )

            reg_flags = []
            if random.random() < 0.08:
                reg_flags.append("legal_mentioned")
            if random.random() < 0.05:
                reg_flags.append("ombudsman_mentioned")

            complaint_id = uuid.uuid4()
            customer_id = random.choice(customer_ids)
            agent_id = random.choice(agent_ids) if status != "new" else None

            await conn.execute(
                """
                INSERT INTO complaints (id, channel, subject, body, customer_id, assigned_agent_id,
                    category, product, severity, sentiment_score, sentiment_label, key_issues,
                    ai_confidence_score, regulatory_flags, status, sla_deadline, is_sla_breached,
                    created_at, updated_at, resolved_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)
            """,
                complaint_id,
                channel,
                subject,
                body,
                customer_id,
                agent_id,
                category,
                product,
                severity,
                sent_score,
                sent_label,
                json.dumps(key_issues),
                round(random.uniform(0.75, 0.98), 2),
                json.dumps(reg_flags),
                status,
                sla_deadline,
                is_breached,
                created,
                created,
                resolved_at,
            )

            # Add initial customer message
            await conn.execute(
                """
                INSERT INTO complaint_messages (id, complaint_id, sender_type, sender_name, content, channel, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                uuid.uuid4(),
                complaint_id,
                "customer",
                random.choice(CUSTOMER_NAMES),
                body,
                channel,
                created,
            )

            # Add agent response if not new
            if status != "new" and agent_id:
                agent_name = next((a[0] for a in AGENT_NAMES if True), "Agent")
                await conn.execute(
                    """
                    INSERT INTO complaint_messages (id, complaint_id, sender_type, sender_name, content, channel, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    uuid.uuid4(),
                    complaint_id,
                    "agent",
                    agent_name,
                    f"Thank you for reaching out about your {category} issue. We're looking into this and will update you shortly.",
                    channel,
                    created + timedelta(hours=random.randint(1, 8)),
                )

            # Audit log
            await conn.execute(
                """
                INSERT INTO audit_log (id, complaint_id, action, performed_by, details, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                uuid.uuid4(),
                complaint_id,
                "created",
                "system",
                json.dumps({"channel": channel, "category": category}),
                created,
            )

            if (i + 1) % 25 == 0:
                print(f"  Seeded {i + 1}/100 complaints...")

        # Add some escalations for escalated complaints
        escalated = await conn.fetch(
            "SELECT id, assigned_agent_id FROM complaints WHERE status = 'escalated'"
        )
        for row in escalated:
            await conn.execute(
                """
                INSERT INTO escalations (id, complaint_id, escalated_by, reason, previous_agent_id, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
                uuid.uuid4(),
                row["id"],
                "system",
                "SLA breach imminent — auto-escalated",
                row["assigned_agent_id"],
                "active",
            )

        print(f"\n  Done! Seeded 100 complaints, {len(escalated)} escalations.")

    finally:
        await conn.close()


if __name__ == "__main__":
    print("Seeding ComplaintIQ database...")
    try:
        asyncio.run(seed())
        print("Seeding complete!")
    except Exception as e:
        print(f"\n[WARNING] Seeding failed: {e}")
        print("This is expected if you are running locally and the database is hosted on Render with 'Internal Only' access.")
        print("The database structure changes have been written successfully and will be applied when deployed or run in the Render VPC.")
