import uuid
from google import genai
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.complaint import Complaint, ComplaintEmbedding
from app.schemas.schemas import SimilarComplaint

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None


async def generate_embedding(text: str) -> list[float] | None:
    """Generate an embedding vector for the given text."""
    if not client:
        return None
    try:
        response = await client.aio.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as e:
        import logging
        logger = logging.getLogger("duplicate_detector")
        logger.warning(f"Failed to generate embedding with Gemini: {e}")
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

    similar = []
    for row in rows:
        cid = uuid.UUID(str(row.complaint_id))
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
                    similarity_score=round(float(row.similarity_score), 3),
                    created_at=c.created_at,
                )
            )
    return similar
