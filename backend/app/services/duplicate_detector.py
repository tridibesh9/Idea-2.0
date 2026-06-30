import uuid
from google import genai
from sqlalchemy import or_, and_, select, text
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
        config = {}
        if "gemini-embedding" in settings.EMBEDDING_MODEL:
            config["output_dimensionality"] = 768
            
        response = await client.aio.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=text,
            config=config,
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
    source_embedding: list[float] | None = None,
    source_entities: list[dict] | None = None,
) -> list[SimilarComplaint]:
    """Find similar complaints using cosine similarity on embeddings."""

    embedding_val = source_embedding
    if embedding_val is None:
        # Get the embedding for this complaint
        result = await db.execute(
            select(ComplaintEmbedding).where(ComplaintEmbedding.complaint_id == complaint_id)
        )
        source_embedding_obj = result.scalar_one_or_none()
        if not source_embedding_obj or source_embedding_obj.embedding is None:
            return []
        embedding_val = source_embedding_obj.embedding

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
            "source_embedding": str(embedding_val.tolist()) if hasattr(embedding_val, "tolist") else str(embedding_val),
            "complaint_id": str(complaint_id),
            "threshold": threshold,
            "limit": limit,
        },
    )
    rows = result.all()

    # Fetch entities for the source complaint if not provided
    source_entities_list = source_entities
    if source_entities_list is None:
        entities_result = await db.execute(
            select(Entity).where(Entity.complaint_id == complaint_id, Entity.is_sensitive == False)
        )
        source_entities_objs = entities_result.scalars().all()
        source_entities_list = [{"entity_type": e.entity_type, "entity_value": e.entity_value} for e in source_entities_objs]
    
    entity_matches = set()
    if source_entities_list:
        # Build query to find complaints sharing the exact same entity type and value
        or_conditions = []
        for ent in source_entities_list:
            ent_type = ent.get("entity_type")
            ent_val = ent.get("entity_value")
            if ent_type and ent_val:
                or_conditions.append(and_(Entity.entity_type == ent_type, Entity.entity_value == ent_val))
        
        if or_conditions:
            match_query = select(Entity.complaint_id).where(Entity.complaint_id != complaint_id, or_(*or_conditions))
            match_res = await db.execute(match_query)
            entity_matches = set(match_res.scalars().all())

    # Collect all candidate complaint IDs
    candidate_ids = set()
    for row in rows:
        candidate_ids.add(uuid.UUID(str(row.complaint_id)))
    for cid in entity_matches:
        candidate_ids.add(cid)

    # Bulk query all complaints
    complaints_map = {}
    if candidate_ids:
        c_result = await db.execute(
            select(Complaint).where(Complaint.id.in_(list(candidate_ids)))
        )
        for c in c_result.scalars().all():
            complaints_map[c.id] = c

    # Compile the final similar list, boosting scores for entity matches
    similar = []
    
    # Track which complaint IDs we've added to avoid duplicates if they appear in both vectors and entities
    processed_cids = set()

    for row in rows:
        cid = uuid.UUID(str(row.complaint_id))
        processed_cids.add(cid)
        c = complaints_map.get(cid)
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
            c = complaints_map.get(cid)
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
