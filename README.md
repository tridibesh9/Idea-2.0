# ComplaintIQ — Unified Customer Complaint Communication Dashboard

## Problem Statement
This project addresses PS5: Unified Customer Complaints Communication Dashboard powered by Gen-AI that aggregates complaints from multiple channels into a single platoform. Our solution **ComplaintIQ** aggregates complaints from multiple channels into a single intelligent platform.

## Demo
The dashboard is accessible locally at `http://localhost:5173` (Vite dev server) or `http://localhost:3000` (Docker Compose). It provides a real-time live feed of incoming complaints, SLA breach tracking, and RAG-powered draft response controls.

---
## Tech Stack
| Layer          | Technology                                |
| -------------- | ----------------------------------------- |
| **Frontend**   | React 18 + Vite + Tailwind CSS + Recharts |
| **Backend**    | FastAPI (Python 3.11)                     |
| **Database**   | PostgreSQL + pgvector (vector DB)         |
| **AI/LLM**     | Google Gemini 2.0/2.5 Flash API           |
| **Embeddings** | Google gemini-embedding-2 (with MRL 768-dim) |
| **Real-time**  | WebSockets (FastAPI)                      |
| **Auth**       | JWT (simple authentication)               |
| **Deployment** | Docker Compose (local demo)               |

---
## How to Run Locally

1. Clone the repository.
2. Create a `.env` file in the `backend` directory with the following environment variables from `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Start the backend:
   ```bash
   cd backend
   python -m venv venv
   python -m pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
4. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
IdeaHackathon/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app + lifespan + routers
│   │   ├── config.py                # Settings (env vars)
│   │   ├── database.py              # SQLAlchemy async setup
│   │   ├── models/                  # 8 SQLAlchemy models
│   │   │   ├── complaint.py         # Complaint, ComplaintMessage, ComplaintEmbedding
│   │   │   ├── customer.py          # Customer
│   │   │   ├── agent.py             # Agent
│   │   │   ├── category.py          # Category
│   │   │   ├── escalation.py        # Escalation
│   │   │   ├── sla_config.py        # SLAConfig
│   │   │   ├── knowledge.py         # KnowledgeDocument (RAG)
│   │   │   └── audit_log.py         # AuditLog
│   │   ├── routes/                  # API endpoints
│   │   │   ├── complaints.py        # CRUD + classification + responses
│   │   │   ├── analytics.py         # Trends & root cause insights
│   │   │   ├── escalations.py       # Escalation management
│   │   │   ├── audit.py             # Audit log queries
│   │   │   ├── reports.py           # Report generation
│   │   │   ├── knowledge.py         # Knowledge Base search & management
│   │   │   ├── simulator.py         # Test data generation & channel mocks
│   │   │   └── websocket.py         # Real-time WebSocket manager
│   │   ├── services/                # Business logic
│   │   │   ├── classifier.py        # Complaint classification (Gemini)
│   │   │   ├── response_generator.py # Draft response generation (Gemini)
│   │   │   ├── duplicate_detector.py# Similar complaint detection (embeddings)
│   │   │   ├── smart_router.py      # Workload-balanced agent routing
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
│   └── generate_complaints.py       # Script to generate test data
└── README.md                        # This file
```

---
## Features
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
- ✅ **RAG-Powered Knowledge Base**: Dynamically retrieves relevant company support policies using pgvector semantic search to guide Gemini draft responses.
- ✅ **Iterative Response Refinement**: Allows agents to iteratively refine Gemini response drafts using natural language commands (e.g. *"offer a refund and apologize"*).
- ✅ **Interactive PCA Cluster Mapping**: Reductions of high-dimensional complaint embeddings to 2D coordinates using Principal Component Analysis (PCA) and K-Means clustering, rendered as an interactive Recharts scatter map on the dashboard.
- ✅ **Workload-Balanced Smart Routing**: Automatically routes and assigns incoming complaints to agents in relevant departments based on their current active workload.
- ✅ **Two-Way Channel Simulator**: Interactive simulator for testing incoming/outgoing communications across mock Email and Telegram channels.

---
## Dataset
The system uses an evaluation dataset generated via the seeding tool [generate_complaints.py](file:///d:/Projects/Idea-2.0/seed/generate_complaints.py):
- **100 complaints** mapping across 6 categories (`billing`, `product_defect`, `service_delay`, `account_access`, `delivery`, `refund`).
- **5 channels** covering Email threads, Telegram webhook payload simulations, Web Form posts, Twitter posts, and Phone transcript snippets.
- **17 pre-configured SLA escalation records** based on historic breaches.
- **6 corporate policy documents** indexed within the vector DB to ground Gemini's Retrieval-Augmented Generation (RAG) replies.

---
## Known Limitations
- **Gemini API Rate Limiting**: The system falls back to rules-based classification and default draft response templates under extreme Gemini API Studio rate limits (free tier RPM/TPM).
- **In-Memory PCA / Clustering**: principal component reductions (PCA) and K-Means coordinates are calculated dynamically in-memory. Massive production scales should move this logic to a decoupled background task.
- **WebSocket State**: The current server keeps active socket connections in local memory. Real-world multi-node horizontal scaling requires a message broker (e.g., Redis Pub/Sub) to synchronize feed signals.
- **Mock Intake Channels**: IMAP/SMTP polling and Telegram Bot listeners are disabled by default for the local build. The application includes a simulator module on the UI to test ingest behavior.

---
## Team

1. Trdidibesh Sarkar
2. Aryaan Sinha
3. Arnab Das
4. Sayan Ghosh

## Contact
For any queries about this submission:

- Team Name: Overclocked4
- Institute: Indian Institute of Technology, Kharagpur
- Email: aryaan.sinha100@gmail.com, bytemysticop@gmail.com
- iDEA 2.0 Phase 2 Submission