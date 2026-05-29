import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.knowledge import KnowledgeDocument
from app.schemas.schemas import KnowledgeCreate, KnowledgeResponse
from app.services.duplicate_detector import generate_embedding

router = APIRouter()

@router.post("", response_model=KnowledgeResponse, status_code=201)
async def create_knowledge_document(
    payload: KnowledgeCreate, db: AsyncSession = Depends(get_db)
):
    # Check if we can generate embedding
    embedding_vector = await generate_embedding(payload.content)
    if not embedding_vector:
        # Generate a dummy 768 float array if API is offline
        embedding_vector = [0.0] * 768

    doc = KnowledgeDocument(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        embedding=embedding_vector
    )
    db.add(doc)
    await db.flush()
    return doc

@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeDocument))
    return result.scalars().all()

@router.get("/search", response_model=list[KnowledgeResponse])
async def search_knowledge_documents(
    q: str,
    category: Optional[str] = None,
    limit: int = 3,
    db: AsyncSession = Depends(get_db)
):
    embedding_vector = await generate_embedding(q)
    if not embedding_vector:
        # Fallback to text search if API key missing
        query = select(KnowledgeDocument)
        if category:
            query = query.where(KnowledgeDocument.category == category)
        query = query.where(
            (KnowledgeDocument.title.contains(q)) | (KnowledgeDocument.content.contains(q))
        ).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    # pgvector cosine similarity search
    if category:
        sql = text("""
            SELECT kd.id, kd.title, kd.content, kd.category
            FROM knowledge_documents kd
            WHERE kd.category = :category
            ORDER BY kd.embedding <=> :query_embedding
            LIMIT :limit
        """)
        params = {
            "query_embedding": str(embedding_vector),
            "category": category,
            "limit": limit
        }
    else:
        sql = text("""
            SELECT kd.id, kd.title, kd.content, kd.category
            FROM knowledge_documents kd
            ORDER BY kd.embedding <=> :query_embedding
            LIMIT :limit
        """)
        params = {
            "query_embedding": str(embedding_vector),
            "limit": limit
        }

    result = await db.execute(sql, params)
    rows = result.all()
    
    docs = []
    for row in rows:
        docs.append(
            KnowledgeDocument(
                id=uuid.UUID(str(row.id)),
                title=row.title,
                content=row.content,
                category=row.category
            )
        )
    return docs
