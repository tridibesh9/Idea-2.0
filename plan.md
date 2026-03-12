# ComplaintIQ — Build Plan

## Project: Unified Customer Complaint Communication Dashboard

---

## Tech Stack

| Layer        | Technology                          |
|-------------|-------------------------------------|
| Frontend    | React 18 + Tailwind CSS + Recharts  |
| Backend     | FastAPI (Python)                    |
| Database    | PostgreSQL + pgvector               |
| AI/LLM      | OpenAI GPT-4o API                  |
| Embeddings  | OpenAI text-embedding-3-small       |
| Real-time   | WebSockets (FastAPI)               |
| Auth        | JWT (simple, for demo)             |
| Deployment  | Docker Compose (local demo)        |

---

## Phase 1: Foundation & Data Layer

### Step 1.1 — Project Scaffolding
**Deliverable:** Monorepo with backend and frontend folders, Docker Compose file, environment config.

```
Idea2.0/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── schemas/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── seed/
│   └── generate_complaints.py
├── Project.md
└── plan.md
```

**Tasks:**
- [ ] Initialize FastAPI backend with project structure
- [ ] Initialize React frontend with Tailwind CSS
- [ ] Create docker-compose.yml (PostgreSQL + pgvector, backend, frontend)
- [ ] Create .env.example with all required env vars

---

### Step 1.2 — Database Schema
**Deliverable:** PostgreSQL schema with all tables, pgvector extension enabled.

**Tables:**
1. `complaints` — core complaint record
2. `complaint_messages` — full communication history per complaint
3. `customers` — customer profiles
4. `agents` — agent/user profiles
5. `categories` — complaint categories
6. `escalations` — escalation records
7. `sla_configs` — SLA rules per category/severity
8. `audit_log` — all actions for regulatory compliance
9. `complaint_embeddings` — vector store for duplicate detection

**Key Fields for `complaints`:**
- id, external_id, channel (email/chat/twitter/phone/form)
- customer_id, assigned_agent_id
- category, product, severity (critical/high/medium/low)
- sentiment_score (-1.0 to 1.0), sentiment_label
- status (new/open/in_progress/escalated/resolved/closed)
- ai_confidence_score
- sla_deadline, is_sla_breached
- created_at, updated_at, resolved_at

**Tasks:**
- [ ] Write SQLAlchemy models for all tables
- [ ] Create Alembic migration
- [ ] Enable pgvector extension
- [ ] Test DB connection and migration

---

### Step 1.3 — Seed Data Generator
**Deliverable:** Script that generates 100 realistic complaints across 5 channels using GPT.

**Tasks:**
- [ ] Write `seed/generate_complaints.py` using OpenAI API
- [ ] Generate complaints for categories: billing, product_defect, service_delay, account_access, delivery, refund
- [ ] Generate across channels: email, twitter, chat, phone_transcript, web_form
- [ ] Include varying severities and sentiments
- [ ] Insert into database with embeddings

---

## Phase 2: AI/NLP Pipeline

### Step 2.1 — Complaint Classification Service
**Deliverable:** API endpoint that accepts raw complaint text and returns structured classification.

**Input:** Raw complaint text + channel
**Output:**
```json
{
  "category": "billing",
  "product": "Credit Card",
  "severity": "high",
  "sentiment_score": -0.8,
  "sentiment_label": "negative",
  "key_issues": ["overcharged", "recurring fee"],
  "confidence": 0.92,
  "regulatory_flags": ["ombudsman_mentioned"]
}
```

**Tasks:**
- [ ] Create `services/classifier.py` with LLM prompt for classification
- [ ] Implement structured output parsing (JSON mode)
- [ ] Add confidence scoring
- [ ] Add regulatory keyword flagging (legal, regulator, ombudsman, lawsuit)
- [ ] Create POST `/api/complaints/classify` endpoint
- [ ] Write unit tests with sample complaints

---

### Step 2.2 — Duplicate/Related Complaint Detection
**Deliverable:** Service that finds semantically similar complaints using vector similarity.

**Tasks:**
- [ ] Create `services/duplicate_detector.py`
- [ ] On complaint ingestion, generate embedding via OpenAI API
- [ ] Store embedding in `complaint_embeddings` table (pgvector)
- [ ] Query top-5 similar complaints (cosine similarity > 0.85 = duplicate, > 0.70 = related)
- [ ] Create GET `/api/complaints/{id}/similar` endpoint
- [ ] Return similarity scores with results

---

### Step 2.3 — Auto-Response Generator
**Deliverable:** Service that drafts a response for agent review.

**Tasks:**
- [ ] Create `services/response_generator.py`
- [ ] Prompt includes: complaint text, category, severity, customer history, resolution templates
- [ ] Support tone parameter: "formal", "empathetic", "neutral"
- [ ] Create POST `/api/complaints/{id}/generate-response` endpoint
- [ ] Response includes: draft_text, tone, suggested_actions
- [ ] Agent can edit before sending (frontend handles this)

---

### Step 2.4 — Trend Analysis & Root Cause Engine
**Deliverable:** Service that generates AI-powered insights from complaint data.

**Tasks:**
- [ ] Create `services/analytics.py`
- [ ] Aggregate complaints by category, product, channel, severity over time
- [ ] Feed aggregated data to LLM for root cause summary generation
- [ ] Create GET `/api/analytics/trends` endpoint (time-series data)
- [ ] Create GET `/api/analytics/root-cause` endpoint (AI-generated insight)
- [ ] Create GET `/api/analytics/summary` endpoint (weekly AI summary)

---

## Phase 3: Backend API (Core CRUD + Business Logic)

### Step 3.1 — Complaint CRUD APIs
**Deliverable:** Full REST API for complaint management.

**Endpoints:**
- [ ] POST `/api/complaints` — create + auto-classify + embed
- [ ] GET `/api/complaints` — list with filters (status, category, severity, channel, agent, date range)
- [ ] GET `/api/complaints/{id}` — detail with full history
- [ ] PATCH `/api/complaints/{id}` — update status, assign agent, add notes
- [ ] GET `/api/complaints/{id}/timeline` — full communication timeline
- [ ] POST `/api/complaints/{id}/messages` — add message to thread

---

### Step 3.2 — SLA & Escalation Engine
**Deliverable:** Background service that tracks SLAs and auto-escalates.

**Tasks:**
- [ ] Define SLA rules: Critical=4h, High=8h, Medium=24h, Low=72h
- [ ] Create background task (FastAPI on_event or APScheduler) that checks SLA deadlines every minute
- [ ] Auto-escalate complaints approaching SLA breach (80% of time elapsed)
- [ ] Create `escalations` record with reason and timestamp
- [ ] WebSocket notification on escalation
- [ ] GET `/api/escalations` — list active escalations

---

### Step 3.3 — Regulatory & Audit
**Deliverable:** Audit trail and export capabilities.

**Tasks:**
- [ ] Log every action (classify, assign, respond, escalate, resolve) to `audit_log`
- [ ] GET `/api/audit/{complaint_id}` — audit trail for a complaint
- [ ] GET `/api/reports/export?format=csv` — export complaints for regulatory reporting
- [ ] GET `/api/reports/export?format=pdf` — PDF report generation (using reportlab or weasyprint)
- [ ] Auto-flag complaints with regulatory keywords

---

## Phase 4: Frontend Dashboard

### Step 4.1 — Layout & Navigation
**Deliverable:** App shell with sidebar navigation, responsive layout.

**Pages:**
- [ ] Dashboard (overview)
- [ ] Complaints List
- [ ] Complaint Detail
- [ ] Analytics
- [ ] Escalations
- [ ] Settings

**Tasks:**
- [ ] Set up React Router
- [ ] Build sidebar navigation component
- [ ] Create top header with search bar and notifications bell
- [ ] Responsive layout (Tailwind)

---

### Step 4.2 — Dashboard Overview Page
**Deliverable:** Real-time overview with KPI cards and charts.

**Components:**
- [ ] KPI Cards: Total Open, Critical, SLA Breached, Avg Resolution Time, Sentiment Score
- [ ] Complaint Volume Chart (line chart — last 30 days by channel)
- [ ] Category Distribution (donut chart)
- [ ] Severity Breakdown (bar chart)
- [ ] Recent Complaints List (top 10, clickable)
- [ ] Live Feed (WebSocket — new complaints appear in real-time)

---

### Step 4.3 — Complaints List Page
**Deliverable:** Filterable, sortable complaint table.

**Features:**
- [ ] Table with columns: ID, Channel Icon, Customer, Category, Severity Badge, Sentiment, Status, SLA Countdown, Agent, Date
- [ ] Filters: status, category, severity, channel, date range, agent
- [ ] Sort by any column
- [ ] Search bar (full-text)
- [ ] Pagination
- [ ] Bulk actions: assign agent, change status

---

### Step 4.4 — Complaint Detail Page (360° View)
**Deliverable:** Complete single-complaint view with all context.

**Sections:**
- [ ] Header: Customer name, complaint ID, status badge, severity badge, sentiment gauge
- [ ] Communication Timeline: all messages in chronological order (chat-style)
- [ ] AI Classification Panel: category, product, severity, sentiment, confidence score, key issues
- [ ] Related/Duplicate Complaints Panel: list with similarity scores, clickable
- [ ] SLA Tracker: visual countdown bar with color coding
- [ ] Action Bar: Assign, Escalate, Resolve, Generate AI Response
- [ ] AI Response Modal: generated draft, tone selector, edit area, send button
- [ ] Audit Trail: collapsible log of all actions
- [ ] Customer Profile Sidebar: past complaints, lifetime value, contact info

---

### Step 4.5 — Analytics Page
**Deliverable:** Trend analysis and AI-powered insights.

**Components:**
- [ ] Time-Series Chart: complaint volume over time (filterable by category/product/channel)
- [ ] Severity × Product Heat Map
- [ ] Top Issue Word Cloud (or bar chart of top keywords)
- [ ] AI Root Cause Summary Card (generated text)
- [ ] AI Weekly Summary Card
- [ ] Channel Performance Comparison
- [ ] Resolution Time Trends

---

### Step 4.6 — Escalation Queue Page
**Deliverable:** Dedicated view for escalated/SLA-breached complaints.

**Features:**
- [ ] List of escalated complaints with SLA remaining time
- [ ] Color-coded urgency (red = breached, yellow = near breach)
- [ ] Quick actions: reassign, acknowledge, resolve
- [ ] Escalation history per complaint

---

## Phase 5: Integration & Polish

### Step 5.1 — WebSocket Real-Time Updates
**Deliverable:** Live updates across the dashboard.

**Tasks:**
- [ ] Backend WebSocket endpoint for complaint events
- [ ] Frontend WebSocket hook
- [ ] Live feed on dashboard: new complaints, status changes, escalations
- [ ] Toast notifications for critical events

---

### Step 5.2 — Omnichannel Intake Simulator
**Deliverable:** Demo tool that simulates complaints arriving from different channels.

**Tasks:**
- [ ] Web form submission (direct)
- [ ] Email simulator (mock endpoint that converts email to complaint)
- [ ] Twitter/X simulator (mock tweet submission)
- [ ] Chat simulator (mock live chat widget)
- [ ] Phone transcript simulator (paste/upload transcript)
- [ ] Each channel shows correct icon/badge in the dashboard

---

### Step 5.3 — Final Polish
**Deliverable:** Demo-ready product.

**Tasks:**
- [ ] Loading states and skeletons for all pages
- [ ] Error handling and empty states
- [ ] Dark/light mode toggle (optional, nice to have)
- [ ] Seed database with 100 realistic complaints
- [ ] Test full flow: submit → classify → detect duplicates → assign → respond → resolve
- [ ] Prepare 3-5 minute demo script
- [ ] Record backup demo video (in case of live issues)

---

## Demo Script (3-5 minutes)

1. **Open Dashboard** → Show KPI cards, live feed, charts (10s)
2. **Submit new complaint** via web form → Watch it auto-appear on dashboard (20s)
3. **Click into complaint** → Show AI classification with confidence scores (20s)
4. **Show related complaints** panel → Highlight duplicate detection (15s)
5. **Click "Generate AI Response"** → Show draft → Adjust tone → Edit → Send (30s)
6. **Show SLA tracker** → Demo an escalation scenario (15s)
7. **Navigate to Analytics** → Show trends, root cause AI summary (20s)
8. **Export regulatory report** → Download CSV/PDF (10s)
9. **Closing slide** → Impact: "80% faster triage, 60% faster response, full compliance" (10s)

---

## Judging Criteria Alignment

| Criteria | How We Score |
|----------|-------------|
| **Innovation** | AI-powered triage + semantic duplicate detection + auto-responses with tone control |
| **Technical Complexity** | LLM pipeline, vector DB, real-time WebSockets, multi-channel ingestion |
| **Completeness** | All 7 PS requirements covered with working features |
| **UI/UX** | Clean Tailwind dashboard, real-time updates, intuitive flows |
| **Impact/Business Value** | Quantifiable: reduced triage time, faster resolution, compliance-ready |
| **Demo Quality** | Live data flow, not slides — complaint goes from submission to resolution in real-time |

---

## Environment Variables (.env)

```
DATABASE_URL=postgresql://user:pass@localhost:5432/complaintiq
OPENAI_API_KEY=sk-...
JWT_SECRET=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

---

## Quick Start Commands

```bash
# Start infrastructure
docker-compose up -d

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Seed data
python seed/generate_complaints.py
```

---

**Start with Phase 1, Step 1.1. Tell me when ready and I'll build it.**
