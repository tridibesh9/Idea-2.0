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
    Assigns an incident group ID to a complaint.
    It checks for similar complaints. If a highly similar one exists, it joins its group.
    Otherwise, it creates a new group.
    """
    if similar is None:
        # Use existing duplicate detector to find semantically similar complaints
        similar = await find_similar(complaint_id, db, limit=1, source_embedding=source_embedding)
    
    if similar and similar[0].similarity_score > 0.85:
        # High similarity, let's see if the similar complaint has an incident group
        similar_complaint_id = similar[0].complaint_id
        result = await db.execute(select(Complaint).where(Complaint.id == similar_complaint_id))
        parent = result.scalar_one_or_none()
        
        if parent:
            if parent.incident_group_id:
                return parent.incident_group_id
            else:
                # Parent doesn't have one yet, create a new one for both
                new_group_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
                parent.incident_group_id = new_group_id
                return new_group_id
                
    # No highly similar complaint found, create a new incident group
    return f"INC-{str(uuid.uuid4())[:8].upper()}"
