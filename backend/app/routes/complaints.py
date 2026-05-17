import json
import uuid
import os
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.complaint import Complaint, ComplaintMessage, ComplaintEmbedding
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.schemas.schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintListResponse,
    ComplaintUpdate,
    MessageCreate,
    MessageResponse,
    GenerateResponseRequest,
    GenerateResponseResult,
    SimilarComplaint,
)
from app.services.classifier import classify_complaint
from app.services.duplicate_detector import find_similar, generate_embedding
from app.services.response_generator import generate_response

router = APIRouter()

SLA_HOURS = {"critical": 4, "high": 8, "medium": 24, "low": 72}


@router.post("", response_model=ComplaintResponse, status_code=201)
async def create_complaint(payload: ComplaintCreate, db: AsyncSession = Depends(get_db)):
    # Find or create customer
    customer = None
    if payload.customer_email:
        result = await db.execute(select(Customer).where(Customer.email == payload.customer_email))
        customer = result.scalar_one_or_none()
        if not customer:
            customer = Customer(name=payload.customer_name or "Unknown", email=payload.customer_email)
            db.add(customer)
            await db.flush()

    # Create complaint
    complaint = Complaint(
        channel=payload.channel,
        subject=payload.subject,
        body=payload.body,
        customer_id=customer.id if customer else None,
        status="new",
    )
    db.add(complaint)
    await db.flush()

    # AI Classification (now passes image data if available)
    classification = await classify_complaint(payload.body, payload.channel, payload.image_data)
    complaint.category = classification.category
    complaint.product = classification.product
    complaint.severity = classification.severity
    complaint.sentiment_score = classification.sentiment_score
    complaint.sentiment_label = classification.sentiment_label
    complaint.key_issues = json.dumps(classification.key_issues)
    complaint.ai_confidence_score = classification.confidence
    complaint.regulatory_flags = json.dumps(classification.regulatory_flags)

    # Set SLA deadline
    hours = SLA_HOURS.get(classification.severity, 24)
    complaint.sla_deadline = datetime.now(timezone.utc) + timedelta(hours=hours)

    # Generate and store embedding
    embedding_vector = await generate_embedding(payload.body)
    if embedding_vector:
        emb = ComplaintEmbedding(complaint_id=complaint.id, embedding=embedding_vector)
        db.add(emb)

    # Initial message
    msg = ComplaintMessage(
        complaint_id=complaint.id,
        sender_type="customer",
        sender_name=payload.customer_name or "Customer",
        content=payload.body,
        channel=payload.channel,
    )
    db.add(msg)

    # Save attached image locally
    if payload.image_data:
        try:
            os.makedirs("uploads", exist_ok=True)
            image_data = payload.image_data
            if "," in image_data:
                image_data = image_data.split(",")[1]
            file_path = f"uploads/{complaint.id}.jpg"
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(image_data))
        except Exception as e:
            print(f"Failed to save image attachment: {e}")

    # Audit log
    audit = AuditLog(
        complaint_id=complaint.id,
        action="created",
        performed_by="system",
        details=json.dumps({"channel": payload.channel, "classification": classification.model_dump()}),
    )
    db.add(audit)
    await db.flush()

    # Broadcast via WebSocket
    try:
        from app.routes.websocket import manager
        await manager.broadcast({
            "type": "new_complaint",
            "complaint_id": str(complaint.id),
            "channel": payload.channel,
            "subject": complaint.subject,
            "severity": complaint.severity,
            "category": complaint.category,
        })
    except Exception:
        pass

    return complaint


@router.get("", response_model=ComplaintListResponse)
async def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    channel: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Complaint)
    count_query = select(func.count(Complaint.id))

    if status:
        query = query.where(Complaint.status == status)
        count_query = count_query.where(Complaint.status == status)
    if category:
        query = query.where(Complaint.category == category)
        count_query = count_query.where(Complaint.category == category)
    if severity:
        query = query.where(Complaint.severity == severity)
        count_query = count_query.where(Complaint.severity == severity)
    if channel:
        query = query.where(Complaint.channel == channel)
        count_query = count_query.where(Complaint.channel == channel)

    total = (await db.execute(count_query)).scalar()
    query = query.order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    complaints = result.scalars().all()

    return ComplaintListResponse(items=complaints, total=total, page=page, page_size=page_size)


@router.get("/{id}/image")
async def get_complaint_image(id: uuid.UUID):
    """Retrieve the uploaded image for a complaint, if it exists."""
    file_path = f"uploads/{id}.jpg"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"message": "Image not found"})


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: uuid.UUID, payload: ComplaintUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(complaint, key, value)
    complaint.updated_at = datetime.now(timezone.utc)

    if payload.status == "resolved":
        complaint.resolved_at = datetime.now(timezone.utc)

    # Audit
    audit = AuditLog(
        complaint_id=complaint.id,
        action="updated",
        performed_by="agent",
        details=json.dumps(update_data, default=str),
    )
    db.add(audit)
    await db.flush()

    # Broadcast status change via WebSocket
    try:
        from app.routes.websocket import manager
        await manager.broadcast({
            "type": "status_change",
            "complaint_id": str(complaint.id),
            "status": complaint.status,
            "severity": complaint.severity,
            "subject": complaint.subject,
        })
    except Exception:
        pass

    return complaint


@router.get("/{complaint_id}/timeline", response_model=list[MessageResponse])
async def get_timeline(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplaintMessage)
        .where(ComplaintMessage.complaint_id == complaint_id)
        .order_by(ComplaintMessage.created_at)
    )
    return result.scalars().all()


@router.post("/{complaint_id}/messages", response_model=MessageResponse, status_code=201)
async def add_message(
    complaint_id: uuid.UUID, payload: MessageCreate, db: AsyncSession = Depends(get_db)
):
    # Verify complaint exists
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    msg = ComplaintMessage(
        complaint_id=complaint_id,
        sender_type=payload.sender_type,
        sender_name=payload.sender_name,
        content=payload.content,
        channel=payload.channel,
    )
    db.add(msg)

    # Update complaint status if agent responds
    if payload.sender_type == "agent" and complaint.status == "new":
        complaint.status = "in_progress"
        complaint.updated_at = datetime.now(timezone.utc)

    audit = AuditLog(
        complaint_id=complaint_id,
        action="message_added",
        performed_by=payload.sender_name or payload.sender_type,
        details=json.dumps({"sender_type": payload.sender_type}),
    )
    db.add(audit)
    await db.flush()
    return msg


@router.get("/{complaint_id}/similar", response_model=list[SimilarComplaint])
async def get_similar(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await find_similar(complaint_id, db)


@router.post("/{complaint_id}/generate-response", response_model=GenerateResponseResult)
async def generate_ai_response(
    complaint_id: uuid.UUID,
    payload: GenerateResponseRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    response = await generate_response(complaint, payload.tone)

    audit = AuditLog(
        complaint_id=complaint_id,
        action="ai_response_generated",
        performed_by="system",
        details=json.dumps({"tone": payload.tone}),
    )
    db.add(audit)
    await db.flush()

    return response
