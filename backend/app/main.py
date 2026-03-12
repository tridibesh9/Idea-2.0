from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import complaints, analytics, escalations, audit

settings = get_settings()

app = FastAPI(
    title="ComplaintIQ API",
    description="Unified Customer Complaint Communication Dashboard",
    version="1.0.0",
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


@app.get("/")
async def root():
    return {"message": "ComplaintIQ API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
