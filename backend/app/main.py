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
from app.services.email_listener import start_email_listener, stop_email_listener
from app.services.telegram_listener import start_telegram_listener, stop_telegram_listener

settings = get_settings()
logger = logging.getLogger("complaintiq")

scheduler = AsyncIOScheduler()

# Global reference to email listener task
_email_listener_task = None
_telegram_listener_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — launch SLA checker every 5 minutes
    scheduler.add_job(check_sla_breaches, "interval", minutes=5, id="sla_checker")
    scheduler.start()
    logger.info("SLA background scheduler started")

    # Start email listener if enabled
    global _email_listener_task
    if settings.EMAIL_LISTENER_ENABLED:
        try:
            # Create a broadcast callback for WebSocket
            async def broadcast_email(data):
                try:
                    from app.routes.websocket import manager

                    await manager.broadcast(data)
                except Exception as e:
                    logger.warning(f"Failed to broadcast email event: {e}")

            _email_listener_task = asyncio.create_task(
                start_email_listener(broadcast_email)
            )
            logger.info("Email listener task started")
        except Exception as e:
            logger.error(f"Failed to start email listener: {e}")

    # Start telegram listener if enabled
    global _telegram_listener_task
    if settings.TELEGRAM_LISTENER_ENABLED:
        try:
            # We can reuse the broadcast_email logic, maybe define it outside if we want, or redefine it
            async def broadcast_telegram(data):
                try:
                    from app.routes.websocket import manager
                    await manager.broadcast(data)
                except Exception as e:
                    logger.warning(f"Failed to broadcast telegram event: {e}")
            
            _telegram_listener_task = asyncio.create_task(
                start_telegram_listener(broadcast_telegram)
            )
            logger.info("Telegram listener task started")
        except Exception as e:
            logger.error(f"Failed to start telegram listener: {e}")

    yield

    # Shutdown
    await stop_email_listener()
    if _email_listener_task:
        _email_listener_task.cancel()
        try:
            await _email_listener_task
        except asyncio.CancelledError:
            pass

    await stop_telegram_listener()
    if _telegram_listener_task:
        _telegram_listener_task.cancel()
        try:
            await _telegram_listener_task
        except asyncio.CancelledError:
            pass
            
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
