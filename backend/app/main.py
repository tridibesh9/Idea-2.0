import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.routes import complaints, analytics, escalations, audit
from app.routes import reports, websocket as ws_route, simulator
from app.services.sla_checker import check_sla_breaches

settings = get_settings()
logger = logging.getLogger("complaintiq")

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — launch SLA checker every 5 minutes
    scheduler.add_job(check_sla_breaches, "interval", minutes=5, id="sla_checker")
    scheduler.start()
    logger.info("SLA background scheduler started")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="ComplaintIQ API",
    description="Unified Customer Complaint Communication Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(complaints.router, prefix="/api/complaints", tags=["Complaints"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(escalations.router, prefix="/api/escalations", tags=["Escalations"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(simulator.router, prefix="/api/simulator", tags=["Simulator"])
app.include_router(ws_route.router, tags=["WebSocket"])


@app.get("/")
async def root():
    return {"message": "ComplaintIQ API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
