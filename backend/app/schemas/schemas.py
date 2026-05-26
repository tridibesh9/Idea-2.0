import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ── Complaint Schemas ──


class ComplaintCreate(BaseModel):
    channel: str = Field(..., description="email, chat, twitter, phone, web_form")
    subject: str | None = None
    body: str
    customer_name: str | None = None
    customer_email: str | None = None


class ComplaintClassification(BaseModel):
    category: str | None = None
    product: str | None = None
    severity: str = "medium"
    sentiment_score: float | None = None
    sentiment_label: str | None = None
    key_issues: list[str] = []
    confidence: float | None = None
    regulatory_flags: list[str] = []


class ComplaintUpdate(BaseModel):
    status: str | None = None
    assigned_agent_id: uuid.UUID | None = None
    severity: str | None = None
    category: str | None = None


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    external_id: str | None
    channel: str
    subject: str | None
    body: str
    customer_id: uuid.UUID | None
    assigned_agent_id: uuid.UUID | None
    category: str | None
    product: str | None
    severity: str
    sentiment_score: float | None
    sentiment_label: str | None
    key_issues: str | None
    ai_confidence_score: float | None
    regulatory_flags: str | None
    status: str
    sla_deadline: datetime | None
    is_sla_breached: bool
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None

    class Config:
        from_attributes = True


class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int


# ── Message Schemas ──


class MessageCreate(BaseModel):
    sender_type: str = "agent"  # customer, agent, system
    sender_name: str | None = None
    content: str
    channel: str | None = None


class MessageResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    sender_type: str
    sender_name: str | None
    content: str
    channel: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ── AI Response Schemas ──


class GenerateResponseRequest(BaseModel):
    tone: str = "empathetic"  # formal, empathetic, neutral


class GenerateResponseResult(BaseModel):
    draft_text: str
    tone: str
    suggested_actions: list[str] = []


# ── Email Reply Schema ──


class SendEmailReplyRequest(BaseModel):
    reply_text: str = Field(..., description="The reply message to send")
    subject: str | None = None


class SendEmailReplyResponse(BaseModel):
    success: bool
    message: str
    complaint_id: uuid.UUID


# ── Similar Complaint Schema ──


class SimilarComplaint(BaseModel):
    complaint_id: uuid.UUID
    subject: str | None
    category: str | None
    severity: str
    status: str
    similarity_score: float
    created_at: datetime


# ── Analytics Schemas ──


class TrendDataPoint(BaseModel):
    date: str
    count: int
    category: str | None = None
    channel: str | None = None


class AnalyticsSummary(BaseModel):
    total_open: int
    total_critical: int
    total_sla_breached: int
    avg_resolution_hours: float | None
    avg_sentiment: float | None


class RootCauseInsight(BaseModel):
    summary: str
    top_categories: list[dict]
    top_products: list[dict]
    recommendations: list[str]


# ── Escalation Schemas ──


class EscalationResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    escalated_by: str
    reason: str
    status: str
    created_at: datetime
    resolved_at: datetime | None

    class Config:
        from_attributes = True


# ── Audit Schemas ──


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID | None
    action: str
    performed_by: str
    details: str | None
    created_at: datetime

    class Config:
        from_attributes = True
