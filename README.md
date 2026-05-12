# ComplaintIQ — Unified Customer Complaint Communication Dashboard

**College:** IIT Kharagpur  
**Team:** Overclocked4  
**Team Members:**

1. Trdidibesh Sarkar
2. Aryaan Sinha
3. Arnab Das
4. Sayan Ghosh

---

## Project Overview

ComplaintIQ is a **Gen-AI-powered unified customer complaint dashboard** that aggregates complaints from multiple channels into a single intelligent platform. The system uses **Google Gemini 2.0 Flash API** for NLP, classification, and automated response generation.

### Key Features

- ✅ **Multi-channel complaint aggregation** (email, chat, Twitter, phone, web form)
- ✅ **AI-powered complaint classification** (category, product, severity, sentiment)
- ✅ **Duplicate/similar complaint detection** using embeddings (pgvector)
- ✅ **Automated draft responses** with tone selection (formal, empathetic, neutral)
- ✅ **SLA tracking & escalation** management with background scheduler
- ✅ **Real-time updates** via WebSockets
- ✅ **360° complaint view** with full communication history
- ✅ **Root cause analysis** and trend insights
- ✅ **Audit logging** for compliance & regulatory tracking
- ✅ **Responsive React frontend** with live analytics dashboard

---

## Tech Stack

| Layer          | Technology                                |
| -------------- | ----------------------------------------- |
| **Frontend**   | React 18 + Vite + Tailwind CSS + Recharts |
| **Backend**    | FastAPI (Python 3.11)                     |
| **Database**   | PostgreSQL + pgvector (vector DB)         |
| **AI/LLM**     | Google Gemini 2.0 Flash API               |
| **Embeddings** | Google text-embedding-004                 |
| **Real-time**  | WebSockets (FastAPI)                      |
| **Auth**       | JWT (simple authentication)               |
| **Deployment** | Docker Compose (local demo)               |

---

## Project Structure

```
IdeaHackathon/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app + lifespan + routers
│   │   ├── config.py                # Settings (env vars)
│   │   ├── database.py              # SQLAlchemy async setup
│   │   ├── models/                  # 7 SQLAlchemy models
│   │   │   ├── complaint.py         # Complaint, ComplaintMessage, ComplaintEmbedding
│   │   │   ├── customer.py          # Customer
│   │   │   ├── agent.py             # Agent
│   │   │   ├── category.py          # Category
│   │   │   ├── escalation.py        # Escalation
│   │   │   ├── sla_config.py        # SLAConfig
│   │   │   └── audit_log.py         # AuditLog
│   │   ├── routes/                  # API endpoints
│   │   │   ├── complaints.py        # CRUD + classification + responses
│   │   │   ├── analytics.py         # Trends & root cause insights
│   │   │   ├── escalations.py       # Escalation management
│   │   │   ├── audit.py             # Audit log queries
│   │   │   ├── reports.py           # Report generation
│   │   │   ├── simulator.py         # Test data generation
│   │   │   └── websocket.py         # Real-time WebSocket manager
│   │   ├── services/                # Business logic
│   │   │   ├── classifier.py        # Complaint classification (Gemini)
│   │   │   ├── response_generator.py # Draft response generation (Gemini)
│   │   │   ├── duplicate_detector.py# Similar complaint detection (embeddings)
│   │   │   ├── analytics.py         # Root cause insights (Gemini)
│   │   │   └── sla_checker.py       # Background SLA check (APScheduler)
│   │   └── schemas/                 # Pydantic request/response models
│   ├── alembic/                     # Database migrations
│   ├── requirements.txt             # Python dependencies
│   ├── Dockerfile                   # Container image
│   └── alembic.ini
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── main.jsx                 # Entry point
│   │   ├── App.jsx                  # Root component
│   │   ├── api.js                   # API client (axios)
│   │   ├── components/              # Reusable components
│   │   │   ├── Layout.jsx           # Header + navigation
│   │   │   ├── LiveFeed.jsx         # Real-time complaint feed
│   │   │   ├── Skeleton.jsx         # Loading skeleton
│   │   │   └── Toast.jsx            # Notifications
│   │   ├── context/                 # Theme context
│   │   │   └── ThemeContext.jsx
│   │   ├── pages/                   # Page components
│   │   │   ├── Dashboard.jsx        # Overview stats & charts
│   │   │   ├── ComplaintsList.jsx   # Filterable list
│   │   │   ├── ComplaintDetail.jsx  # Full complaint view + actions
│   │   │   ├── Analytics.jsx        # Insights & trends
│   │   │   ├── Escalations.jsx      # Escalation workflow
│   │   │   └── SubmitComplaint.jsx  # New complaint form
│   │   └── hooks/                   # Custom React hooks
│   │       └── useWebSocket.js      # WebSocket integration
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── Dockerfile
│
├── seed/
│   └── generate_complaints.py       # Script to generate test data
│
├── docker-compose.yml               # Multi-container orchestration
├── .env.example                     # Environment template
├── Project.md                       # Project brief
├── plan.md                          # Development roadmap
├── progress.md                      # Completion status
└── README.md                        # This file
```

---

## Current State & Completion Status

### ✅ Phase 1: Foundation & Data Layer — COMPLETED

- ✅ Project structure initialized (monorepo)
- ✅ FastAPI backend with modular architecture
- ✅ React frontend with Vite + Tailwind
- ✅ 7 SQLAlchemy models with async patterns
- ✅ Alembic migration setup
- ✅ Docker Compose orchestration
- ✅ Environment configuration

### ✅ Phase 2: AI/LLM Integration — COMPLETED

- ✅ Complaint classification (category, product, severity, sentiment)
- ✅ Automated response generation with tone selection
- ✅ Root cause analysis from complaint trends
- ✅ Vector embeddings for duplicate detection
- ✅ Fallback templates when API key unavailable

### ✅ Phase 3: Backend Services & API Routes — COMPLETED

- ✅ Complaint CRUD endpoints
- ✅ Complaint classification endpoint
- ✅ Response generation endpoint
- ✅ Analytics & insights endpoint
- ✅ SLA tracking & background scheduler
- ✅ Escalation management
- ✅ Audit logging
- ✅ WebSocket real-time feeds

### ✅ Phase 4: Frontend Implementation — COMPLETED

- ✅ Dashboard with statistics & charts
- ✅ Complaints list view (filterable)
- ✅ Complaint detail page with actions
- ✅ Analytics page with trends
- ✅ Escalations management UI
- ✅ Submit complaint form
- ✅ Live feed with WebSocket
- ✅ Responsive layout + dark mode support

---

## Google Gemini API Integration

The system integrates **Google Gemini 2.0 Flash API** for three main AI tasks:

### 1. **Complaint Classification** (`classifier.py`)

**What it sends to Gemini:**

```python
{
  "channel": "email",
  "text": "I've been charged twice for my credit card..."
}
```

**What it receives:**

```json
{
  "category": "billing",
  "product": "Credit Card",
  "severity": "high",
  "sentiment_score": -0.8,
  "sentiment_label": "negative",
  "key_issues": ["Duplicate charge on account", "Missing refund confirmation"],
  "confidence": 0.92,
  "regulatory_flags": ["fraud_mentioned"]
}
```

**Response fields:**

- `category` — One of: `billing`, `product_defect`, `service_delay`, `account_access`, `delivery`, `refund`, `fraud`, `general`
- `product` — e.g., "Savings Account", "Mobile App", "Loan"
- `severity` — One of: `critical`, `high`, `medium`, `low` (based on urgency, financial impact, distress level)
- `sentiment_score` — Float from -1.0 (very negative) to 1.0 (very positive)
- `sentiment_label` — One of: `positive`, `neutral`, `negative`
- `key_issues` — 2-4 extracted issue descriptions
- `confidence` — Confidence score (0.0–1.0)
- `regulatory_flags` — Array of flags if detected: `legal_mentioned`, `regulator_mentioned`, `ombudsman_mentioned`, `lawsuit_mentioned`, `discrimination_mentioned`

**Endpoint:** `POST /api/complaints/` (classification happens automatically on create)

---

### 2. **Response Generation** (`response_generator.py`)

**What it sends to Gemini:**

```python
{
  "subject": "Charged twice for subscription",
  "category": "billing",
  "severity": "high",
  "sentiment": "negative",
  "body": "I was charged twice on my credit card...",
  "tone": "empathetic"
}
```

**What it receives:**

```json
{
  "draft_text": "Hi there,\n\nI'm sorry to hear about the duplicate charge on your account. That's definitely frustrating, and I completely understand...",
  "tone": "empathetic",
  "suggested_actions": [
    "Review account transaction history",
    "Process refund for duplicate charge",
    "Add transaction monitoring alert"
  ]
}
```

**Response fields:**

- `draft_text` — Professional draft response (150–250 words)
- `tone` — Tone used: `formal`, `empathetic`, `neutral`
- `suggested_actions` — 2–3 recommended next steps for the agent

**Endpoint:** `POST /api/complaints/{complaint_id}/generate-response`  
**Parameters:** `tone` (optional, defaults to "empathetic")

---

### 3. **Root Cause Analysis** (`analytics.py`)

**What it sends to Gemini:**

```python
{
  "period_days": 30,
  "total_complaints": 147,
  "categories": [
    {"category": "billing", "count": 42},
    {"category": "service_delay", "count": 31}
  ],
  "products": [
    {"product": "Credit Card", "count": 28}
  ],
  "severities": {
    "critical": 3,
    "high": 15,
    "medium": 89,
    "low": 40
  },
  "avg_sentiment": -0.62
}
```

**What it receives:**

```json
{
  "summary": "Over the last 30 days, billing-related complaints have surged 35% primarily due to incorrect charge calculations on credit card statements. The high volume of service delay complaints (21%) suggests recent outages...",
  "top_categories": [
    { "category": "billing", "count": 42 },
    { "category": "service_delay", "count": 31 }
  ],
  "top_products": [{ "product": "Credit Card", "count": 28 }],
  "recommendations": [
    "Investigate recent billing system update for calculation errors",
    "Prioritize service infrastructure improvements",
    "Implement automated refund processing for duplicate charges"
  ]
}
```

**Response fields:**

- `summary` — 2–3 sentence executive summary
- `top_categories` — Top complaint categories with counts
- `top_products` — Top affected products with counts
- `recommendations` — 3–5 actionable recommendations

**Endpoint:** `GET /api/analytics/insights?days=30`

---

### 4. **Duplicate Detection** (`duplicate_detector.py`)

**Uses:** `text-embedding-004` model (not classification)

**What it sends to Gemini:**

```python
text = "I was charged twice for my subscription..."
```

**What it receives:**

```python
embedding = [0.023, -0.108, 0.445, ...]  # 768-dimensional vector
```

**Purpose:** Stores embedding vectors in PostgreSQL with pgvector extension. Uses cosine similarity (threshold 0.70) to find similar complaints in the database.

**Endpoint:** `GET /api/complaints/{complaint_id}/similar`  
**Returns:** Array of up to 5 similar complaints with similarity scores

**Similar Complaint Response:**

```json
{
  "complaint_id": "uuid",
  "subject": "Double charge on credit card",
  "category": "billing",
  "severity": "high",
  "status": "resolved",
  "similarity_score": 0.87,
  "created_at": "2026-01-15T10:30:00Z"
}
```

---

## API Endpoints

### Complaints

- `POST /api/complaints/` — Create complaint (auto-classifies with Gemini)
- `GET /api/complaints/` — List complaints (filterable)
- `GET /api/complaints/{complaint_id}` — Get complaint detail
- `PUT /api/complaints/{complaint_id}` — Update status, severity, agent
- `POST /api/complaints/{complaint_id}/generate-response` — Generate draft response
- `GET /api/complaints/{complaint_id}/similar` — Find similar complaints

### Analytics

- `GET /api/analytics/insights?days=30` — Root cause analysis & trends
- `GET /api/analytics/dashboard-stats` — Summary stats (total, by category, severity)

### Escalations

- `POST /api/escalations/` — Create escalation
- `GET /api/escalations/` — List escalations
- `PUT /api/escalations/{escalation_id}` — Update escalation status

### Audit

- `GET /api/audit/logs` — Audit log entries
- `GET /api/audit/logs?complaint_id=<id>` — Logs for specific complaint

### WebSocket

- `WS /ws` — Real-time complaint feed & updates

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Google Gemini API Key** ([get here](https://aistudio.google.com/app/apikeys))
- **PostgreSQL client** (optional, for direct DB access)

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Google Gemini API
GEMINI_API_KEY=your-actual-api-key-here
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004

# Database (defaults for docker-compose)
DATABASE_URL=postgresql+asyncpg://complaintiq:complaintiq@db:5432/complaintiq
DATABASE_URL_SYNC=postgresql://complaintiq:complaintiq@db:5432/complaintiq

# Frontend
VITE_API_URL=http://localhost:8000

# CORS
CORS_ORIGINS=http://localhost:3000

# JWT (demo only)
JWT_SECRET=change-me-in-production
```

### 2. Run with Docker Compose (Recommended)

```bash
cd d:\Projects\IdeaHackathon
docker compose up --build
```

This starts:

- **PostgreSQL** on `localhost:5432`
- **FastAPI backend** on `http://localhost:8000`
- **React frontend** on `http://localhost:3000`

**Access:**

- Frontend: http://localhost:3000
- API docs (Swagger): http://localhost:8000/docs
- API redoc: http://localhost:8000/redoc

### 3. Run Backend Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will start on `http://localhost:8000`

### 4. Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:5173`

---

## Database Migrations

Alembic handles schema migrations:

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## Generate Test Data

```bash
cd seed
python generate_complaints.py
```

Creates realistic test complaints in the database for demo purposes.

---

## Key Features Explained

### SLA Tracking & Escalation

- Background job runs every 5 minutes (APScheduler)
- Checks for breached SLA deadlines
- Auto-escalates & creates audit logs
- Broadcasts updates via WebSocket

### Real-time Updates

- WebSocket manager broadcasts changes
- Live feed updates on new complaints
- Escalation notifications
- SLA breach alerts

### Duplicate Detection

- All complaint bodies embedded using `text-embedding-004`
- pgvector stores & queries embeddings
- Cosine similarity search finds similar complaints
- Threshold: 0.70 (configurable)

### Audit Logging

- Every complaint action logged
- Tracks who (agent/system) did what
- Full history searchable
- Regulatory compliance support

---

## Development Notes

### Backend Structure

- **Models** — SQLAlchemy ORM definitions
- **Routes** — FastAPI endpoints with request validation
- **Services** — Business logic (AI, embeddings, SLA checks)
- **Schemas** — Pydantic models for API I/O

### Frontend Structure

- **Pages** — Main application views
- **Components** — Reusable UI components
- **Context** — Shared state (theme, auth)
- **Hooks** — Custom React hooks (WebSocket, API)
- **API** — Centralized axios client

### Configuration

- `config.py` loads environment variables
- Falls back to `.env` file
- Supports both Render postgres and local postgres

---

## Troubleshooting

### Backend won't start

1. Ensure you're in the `backend/` directory
2. Check `GEMINI_API_KEY` is set in `.env`
3. Verify PostgreSQL is running
4. Check port 8000 is not in use

### Frontend won't connect to backend

1. Verify backend is running on `localhost:8000`
2. Check `CORS_ORIGINS` includes frontend URL
3. Clear browser cache and restart dev server

### Database connection errors

1. Ensure PostgreSQL container is healthy
2. Check connection string in `.env`
3. Run migrations: `alembic upgrade head`

### Gemini API key errors

1. Verify API key is valid at https://aistudio.google.com/app/apikeys
2. Ensure it has the correct scopes
3. Check for rate limiting (free tier has limits)

---

## License & Attribution

Built by **Overclocked4** for IIT Kharagpur during Idea Hackathon.

---

## Contacts

- **GitHub:** [Overclocked4 Team]
- **Email:** [team@overclocked4.dev]

_Last updated: March 20, 2026_
