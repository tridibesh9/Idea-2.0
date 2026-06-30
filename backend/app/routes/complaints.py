import json
import uuid
import os
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import select, func, update, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.complaint import Complaint, ComplaintMessage, ComplaintEmbedding
from app.models.customer import Customer
from app.models.audit_log import AuditLog
from app.models.entity import Entity
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
    SendEmailReplyRequest,
    SendEmailReplyResponse,
)
from app.services.classifier import classify_complaint
from app.services.duplicate_detector import find_similar, generate_embedding
from app.services.response_generator import generate_response
from app.services.email_sender import send_reply_email
from app.services.telegram_sender import send_telegram_reply
from app.services.pii_redactor import pii_redactor
from app.services.entity_extractor import extract_entities
from app.services.grouping_engine import assign_incident_group
from app.services.complaint_pipeline import process_complaint_pipeline
from app.services.analytics_cache import analytics_cache

router = APIRouter()

SLA_HOURS = {"critical": 4, "high": 8, "medium": 24, "low": 72}


@router.post("", response_model=ComplaintResponse, status_code=201)
async def create_complaint(
    payload: ComplaintCreate, db: AsyncSession = Depends(get_db)
):
    # Find or create customer
    customer = None
    if payload.customer_email:
        result = await db.execute(
            select(Customer).where(Customer.email == payload.customer_email)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            customer = Customer(
                name=payload.customer_name or "Unknown", email=payload.customer_email
            )
            db.add(customer)
            await db.flush()

    # Run unified functional pipeline
    complaint_id = uuid.uuid4()
    pipeline_result = await process_complaint_pipeline(
        text=payload.body,
        channel=payload.channel,
        db=db,
        image_base64=payload.image_data,
        complaint_id=complaint_id,
    )

    # Create complaint using the generated ID
    complaint = Complaint(
        id=pipeline_result.complaint_id,
        channel=payload.channel,
        subject=payload.subject or pipeline_result.classification.subject,
        body=payload.body,
        customer_id=customer.id if customer else None,
        status="new",
    )
    db.add(complaint)
    await db.flush()

    # Save entities
    for token_type, tokens in pipeline_result.sensitive_entities.items():
        for val in tokens:
            db.add(Entity(complaint_id=complaint.id, entity_type=token_type, entity_value=val, is_sensitive=True))
    for be in pipeline_result.classification.entities:
        db.add(Entity(complaint_id=complaint.id, entity_type=be.get("entity_type"), entity_value=be.get("entity_value"), is_sensitive=False))

    # Save classification fields
    complaint.category = pipeline_result.classification.category
    complaint.product = pipeline_result.classification.product
    complaint.severity = pipeline_result.classification.severity
    complaint.sentiment_score = pipeline_result.classification.sentiment_score
    complaint.sentiment_label = pipeline_result.classification.sentiment_label
    complaint.key_issues = json.dumps(pipeline_result.classification.key_issues)
    complaint.ai_confidence_score = pipeline_result.classification.confidence
    complaint.regulatory_flags = json.dumps(pipeline_result.classification.regulatory_flags)
    complaint.next_best_action = getattr(pipeline_result.classification, "next_best_action", None)

    # Set SLA deadline
    hours = SLA_HOURS.get(pipeline_result.classification.severity, 24)
    complaint.sla_deadline = datetime.now(timezone.utc) + timedelta(hours=hours)

    # Smart Routing Auto Assignment
    from app.services.smart_router import route_complaint
    await route_complaint(complaint, db)

    # Store embedding if generated
    if pipeline_result.embedding:
        emb = ComplaintEmbedding(complaint_id=complaint.id, embedding=pipeline_result.embedding)
        db.add(emb)
        await db.flush()
        
        # Grouping Engine: Assign Incident Group based on similarity
        complaint.incident_group_id = await assign_incident_group(
            complaint.id, 
            db, 
            source_embedding=pipeline_result.embedding,
            similar=pipeline_result.similar_complaints
        )

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
        details=json.dumps(
            {"channel": payload.channel, "classification": pipeline_result.classification.model_dump()}
        ),
    )
    db.add(audit)
    await db.flush()

    # Broadcast via WebSocket
    try:
        from app.routes.websocket import manager

        await manager.broadcast(
            {
                "type": "new_complaint",
                "complaint_id": str(complaint.id),
                "channel": payload.channel,
                "subject": complaint.subject,
                "severity": complaint.severity,
                "category": complaint.category,
            }
        )
    except Exception:
        pass

    analytics_cache.invalidate_all()
    await db.refresh(complaint, attribute_names=["entities"])
    return complaint


@router.get("", response_model=ComplaintListResponse)
async def list_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    channel: Optional[str] = None,
    assigned_agent_id: Optional[uuid.UUID] = None,
    prioritize_dept: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Complaint).options(selectinload(Complaint.entities))
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
    if assigned_agent_id:
        query = query.where(Complaint.assigned_agent_id == assigned_agent_id)
        count_query = count_query.where(Complaint.assigned_agent_id == assigned_agent_id)

    total = (await db.execute(count_query)).scalar()

    # Sort matching department categories at higher priority
    if prioritize_dept:
        from app.services.smart_router import CATEGORY_TO_DEPARTMENT
        dept_categories = [cat for cat, dept in CATEGORY_TO_DEPARTMENT.items() if dept == prioritize_dept]
        if dept_categories:
            dept_case = case(
                (Complaint.category.in_(dept_categories), 0),
                else_=1
            )
            query = query.order_by(dept_case, Complaint.created_at.desc())
        else:
            query = query.order_by(Complaint.created_at.desc())
    else:
        query = query.order_by(Complaint.created_at.desc())

    query = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    complaints = result.scalars().all()

    return ComplaintListResponse(
        items=complaints, total=total, page=page, page_size=page_size
    )


@router.get("/{id}/image")
async def get_complaint_image(id: uuid.UUID):
    """Retrieve the uploaded image for a complaint, if it exists."""
    file_path = f"uploads/{id}.jpg"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"message": "Image not found"})


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.entities))
        .where(Complaint.id == complaint_id)
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
async def update_complaint(
    complaint_id: uuid.UUID,
    payload: ComplaintUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Complaint)
        .options(selectinload(Complaint.entities))
        .where(Complaint.id == complaint_id)
    )
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

        await manager.broadcast(
            {
                "type": "status_change",
                "complaint_id": str(complaint.id),
                "status": complaint.status,
                "severity": complaint.severity,
                "subject": complaint.subject,
            }
        )
    except Exception:
        pass

    analytics_cache.invalidate_all()
    await db.refresh(complaint, attribute_names=["entities"])
    return complaint


@router.get("/{complaint_id}/timeline", response_model=list[MessageResponse])
async def get_timeline(complaint_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ComplaintMessage)
        .where(ComplaintMessage.complaint_id == complaint_id)
        .order_by(ComplaintMessage.created_at)
    )
    return result.scalars().all()


@router.post(
    "/{complaint_id}/messages", response_model=MessageResponse, status_code=201
)
async def add_message(
    complaint_id: uuid.UUID, payload: MessageCreate, db: AsyncSession = Depends(get_db)
):
    # Verify complaint exists
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    content_to_save = payload.content
    
    # Redact customer messages and evaluate automatic escalation
    if payload.sender_type == "customer":
        from app.services.pii_redactor import pii_redactor
        safe_content, _ = pii_redactor.redact(payload.content)
        content_to_save = safe_content

        # Automatic Escalation check
        try:
            from app.services.classifier import classify_complaint
            from app.models.agent import Agent
            from app.models.escalation import Escalation
            import logging
            
            logger = logging.getLogger("complaints_messages")

            # Run classifier on the customer's message
            classification = await classify_complaint(safe_content, complaint.channel, safe_text=safe_content)
            
            # Check if severity becomes critical or sentiment score decreases rapidly (< -0.7)
            if classification.severity == "critical" or classification.sentiment_score < -0.7:
                # Find Senior Official
                senior_res = await db.execute(select(Agent).where(Agent.email == "senior@complaintiq.com"))
                senior_official = senior_res.scalar_one_or_none()
                
                if senior_official and complaint.assigned_agent_id != senior_official.id:
                    prev_agent_id = complaint.assigned_agent_id
                    complaint.assigned_agent_id = senior_official.id
                    complaint.status = "escalated"
                    complaint.severity = classification.severity
                    complaint.sentiment_score = classification.sentiment_score
                    complaint.sentiment_label = classification.sentiment_label
                    
                    escalation = Escalation(
                        complaint_id=complaint.id,
                        escalated_by="system",
                        reason=f"Automatic escalation: Customer message severity escalated to critical or sentiment dropped rapidly (sentiment score: {classification.sentiment_score}).",
                        previous_agent_id=prev_agent_id,
                        new_agent_id=senior_official.id,
                        status="active"
                    )
                    db.add(escalation)
                    
                    esc_audit = AuditLog(
                        complaint_id=complaint.id,
                        action="complaint_escalated",
                        performed_by="system",
                        details=json.dumps({
                            "reason": "Automatic severity/sentiment escalation",
                            "severity": classification.severity,
                            "sentiment_score": classification.sentiment_score
                        })
                    )
                    db.add(esc_audit)
                    logger.info(f"Automatically escalated complaint {complaint.id} to Senior Official.")
        except Exception as e:
            import logging
            logging.getLogger("complaints_messages").error(f"Error checking automatic escalation: {e}")

    msg = ComplaintMessage(
        complaint_id=complaint_id,
        sender_type=payload.sender_type,
        sender_name=payload.sender_name,
        content=content_to_save,
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

    response = await generate_response(
        complaint, 
        tone=payload.tone, 
        db=db, 
        instruction=payload.instruction, 
        current_draft=payload.current_draft
    )

    audit = AuditLog(
        complaint_id=complaint_id,
        action="ai_response_generated",
        performed_by="system",
        details=json.dumps({
            "tone": payload.tone,
            "instruction_refined": payload.instruction is not None
        }),
    )
    db.add(audit)
    await db.flush()

    return response


@router.post(
    "/{complaint_id}/send-reply", response_model=SendEmailReplyResponse, status_code=200
)
async def send_email_reply(
    complaint_id: uuid.UUID,
    payload: SendEmailReplyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a reply to the customer for a complaint (via email or telegram)."""
    # Get complaint with customer info
    result = await db.execute(
        select(Complaint)
        .where(Complaint.id == complaint_id)
        .options(
            selectinload(Complaint.customer),
            selectinload(Complaint.messages),
        )
    )
    complaint = result.scalar_one_or_none()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if not complaint.customer or not complaint.customer.email:
        raise HTTPException(status_code=400, detail="Customer email not available")

    if complaint.channel not in ["email", "telegram"]:
        raise HTTPException(
            status_code=400, detail="Can only send replies for email or telegram channel complaints"
        )

    if complaint.channel == "email":
        # Get the first email message from customer for threading
        original_message_id = complaint.external_id
        original_references = ""

        # Prepare subject
        subject = payload.subject or complaint.subject or "Your Support Request"

        # Send email
        success = await send_reply_email(
            recipient=complaint.customer.email,
            subject=subject,
            body_text=payload.reply_text,
            original_complaint_id=str(complaint_id),
            original_message_id=original_message_id,
            original_references=original_references,
        )
    elif complaint.channel == "telegram":
        chat_id = complaint.external_id
        subject = payload.subject or complaint.subject or "Reply"
        markup = {
            "inline_keyboard": [
                [{"text": f"↩️ Reply to Ticket {str(complaint_id)[:8]}", "callback_data": f"resume:{str(complaint_id)}"}]
            ]
        }
        success = await send_telegram_reply(chat_id, payload.reply_text, reply_markup=markup)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send reply")

    # Record the reply message in database
    msg = ComplaintMessage(
        complaint_id=complaint_id,
        sender_type="agent",
        sender_name="Support Agent",
        content=payload.reply_text,
        channel="email",
    )
    db.add(msg)

    # Update complaint status if needed
    if complaint.status == "new":
        complaint.status = "in_progress"
    complaint.updated_at = datetime.now(timezone.utc)

    # Create audit log
    audit = AuditLog(
        complaint_id=complaint_id,
        action="reply_sent",
        performed_by="agent",
        details=json.dumps(
            {
                "channel": complaint.channel,
                "recipient": complaint.customer.email if complaint.channel == "email" else complaint.external_id,
                "subject": subject,
            }
        ),
    )
    db.add(audit)
    await db.commit()

    # Broadcast via WebSocket
    try:
        from app.routes.websocket import manager

        await manager.broadcast(
            {
                "type": "reply_sent",
                "complaint_id": str(complaint_id),
                "status": complaint.status,
                "subject": complaint.subject,
            }
        )
    except Exception:
        pass

    return SendEmailReplyResponse(
        success=True,
        message=f"Reply sent via {complaint.channel}",
        complaint_id=complaint_id,
    )


@router.post("/generate-missing-embeddings")
async def generate_missing_embeddings(db: AsyncSession = Depends(get_db)):
    """Generate and save vector embeddings for any existing complaints that lack them."""
    result = await db.execute(
        select(Complaint)
        .outerjoin(ComplaintEmbedding, Complaint.id == ComplaintEmbedding.complaint_id)
        .where(ComplaintEmbedding.complaint_id == None)
    )
    complaints = result.scalars().all()
    
    count = 0
    errors = []
    
    for c in complaints:
        try:
            embedding_vector = await generate_embedding(c.body)
            if embedding_vector:
                emb = ComplaintEmbedding(complaint_id=c.id, embedding=embedding_vector)
                db.add(emb)
                count += 1
            else:
                errors.append(f"Could not generate embedding for Complaint ID {c.id}")
        except Exception as e:
            errors.append(f"Error for Complaint ID {c.id}: {str(e)}")
            
    if count > 0:
        await db.commit()
        
    return {
        "processed": count,
        "total_missing": len(complaints),
        "errors": errors
    }
