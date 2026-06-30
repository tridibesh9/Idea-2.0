import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.complaint import Complaint
from app.services.duplicate_detector import find_similar
from app.schemas.schemas import SimilarComplaint

async def assign_incident_group(
    complaint_id: uuid.UUID,
    db: AsyncSession,
    source_embedding: list[float] | None = None,
    similar: list[SimilarComplaint] | None = None,
) -> str:
    """
    Assigns an incident group ID to a complaint and links the customer if highly similar.
    It checks for similar complaints. If a highly similar one exists (or exact entity match), 
    it joins its group and links the customer.
    Otherwise, it creates a new group.
    """
    if similar is None:
        # Use existing duplicate detector to find semantically similar complaints
        similar = await find_similar(complaint_id, db, limit=1, source_embedding=source_embedding)
    
    if similar and similar[0].similarity_score > 0.85:
        # High similarity, let's see if the similar complaint has an incident group
        similar_complaint_id = similar[0].complaint_id
        
        result_current = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
        current_complaint = result_current.scalar_one_or_none()
        
        result_parent = await db.execute(select(Complaint).where(Complaint.id == similar_complaint_id))
        parent = result_parent.scalar_one_or_none()
        
        if parent and current_complaint:
            # 1. Link customer if parent has one and current doesn't
            if parent.customer_id and not current_complaint.customer_id:
                current_complaint.customer_id = parent.customer_id

            # 2. Assign incident group
            if parent.incident_group_id:
                return parent.incident_group_id
            else:
                # Parent doesn't have one yet, create a new one for both
                new_group_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
                parent.incident_group_id = new_group_id
                return new_group_id
                
    # No highly similar complaint found, create a new incident group
    return f"INC-{str(uuid.uuid4())[:8].upper()}"
