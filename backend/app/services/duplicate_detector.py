import uuid
from google import genai
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.complaint import Complaint, ComplaintEmbedding
from app.models.entity import Entity
from app.schemas.schemas import SimilarComplaint

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None


async def generate_embedding(text: str) -> list[float] | None:
    """Generate an embedding vector for the given text."""
    if not client:
        return None
    try:
        response = await client.aio.models.embed_content(
            model="text-embedding-004",  # Some SDK versions enforce string literals here over config lookups
            contents=text,
        )
        if response and response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding generation failed: {e}. Skipping pgvector similarity for this complaint.")
        return None
    return None


async def find_similar(
    complaint_id: uuid.UUID,
    db: AsyncSession,
    threshold: float = 0.70,
    limit: int = 5,
) -> list[SimilarComplaint]:
    """Find similar complaints using cosine similarity on embeddings."""

    # Get the embedding for this complaint
    result = await db.execute(
        select(ComplaintEmbedding).where(ComplaintEmbedding.complaint_id == complaint_id)
    )
    source_embedding = result.scalar_one_or_none()
    if not source_embedding or source_embedding.embedding is None:
        return []

    # pgvector cosine distance: <=> operator (lower = more similar)
    # cosine similarity = 1 - cosine distance
    query = text("""
        SELECT ce.complaint_id,
               1 - (ce.embedding <=> :source_embedding) AS similarity_score
        FROM complaint_embeddings ce
        WHERE ce.complaint_id != :complaint_id
          AND 1 - (ce.embedding <=> :source_embedding) >= :threshold
        ORDER BY similarity_score DESC
        LIMIT :limit
    """)

    result = await db.execute(
        query,
        {
            "source_embedding": str(source_embedding.embedding),
            "complaint_id": str(complaint_id),
            "threshold": threshold,
            "limit": limit,
        },
    )
    rows = result.all()

    # Fetch entities for the source complaint
    entities_result = await db.execute(
        select(Entity).where(Entity.complaint_id == complaint_id, Entity.is_sensitive == False)
    )
    source_entities = entities_result.scalars().all()
    
    entity_matches = set()
    if source_entities:
        # Build query to find complaints sharing the exact same entity type and value
        from sqlalchemy import or_, and_
        or_conditions = []
        for ent in source_entities:
            or_conditions.append(and_(Entity.entity_type == ent.entity_type, Entity.entity_value == ent.entity_value))
        
        if or_conditions:
            match_query = select(Entity.complaint_id).where(Entity.complaint_id != complaint_id, or_(*or_conditions))
            match_res = await db.execute(match_query)
            entity_matches = set(match_res.scalars().all())

    # Compile the final similar list, boosting scores for entity matches
    similar = []
    
    # Track which complaint IDs we've added to avoid duplicates if they appear in both vectors and entities
    processed_cids = set()

    for row in rows:
        cid = uuid.UUID(str(row.complaint_id))
        processed_cids.add(cid)
        complaint_result = await db.execute(select(Complaint).where(Complaint.id == cid))
        c = complaint_result.scalar_one_or_none()
        if c:
            # Boost score to 1.0 if it's an exact entity match, otherwise use vector similarity
            final_score = 1.0 if cid in entity_matches else float(row.similarity_score)
            
            similar.append(
                SimilarComplaint(
                    complaint_id=c.id,
                    subject=c.subject,
                    category=c.category,
                    severity=c.severity,
                    status=c.status,
                    similarity_score=round(final_score, 3),
                    created_at=c.created_at,
                )
            )

    # Add any entity matches that didn't meet the vector threshold
    for cid in entity_matches:
        if cid not in processed_cids:
            complaint_result = await db.execute(select(Complaint).where(Complaint.id == cid))
            c = complaint_result.scalar_one_or_none()
            if c:
                similar.append(
                    SimilarComplaint(
                        complaint_id=c.id,
                        subject=c.subject,
                        category=c.category,
                        severity=c.severity,
                        status=c.status,
                        similarity_score=1.0,  # Explicit entity match gets perfect score
                        created_at=c.created_at,
                    )
                )

    # Sort again by score descending since we might have added new ones or boosted scores
    similar.sort(key=lambda x: x.similarity_score, reverse=True)
    
    # Re-apply limit after merging
    return similar[:limit]
