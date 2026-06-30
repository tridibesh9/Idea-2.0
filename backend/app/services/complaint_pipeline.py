import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.pii_redactor import pii_redactor
from app.services.classifier import classify_complaint
from app.services.duplicate_detector import generate_embedding, find_similar
from app.schemas.schemas import ComplaintClassification, SimilarComplaint

class ProcessedComplaintResult:
    def __init__(
        self,
        complaint_id: uuid.UUID,
        safe_text: str,
        sensitive_entities: dict,
        classification: ComplaintClassification,
        embedding: list[float] | None,
        similar_complaints: list[SimilarComplaint]
    ):
        self.complaint_id = complaint_id
        self.safe_text = safe_text
        self.sensitive_entities = sensitive_entities
        self.classification = classification
        self.embedding = embedding
        self.similar_complaints = similar_complaints

async def process_complaint_pipeline(
    text: str,
    channel: str,
    db: AsyncSession,
    image_base64: str | None = None,
    complaint_id: uuid.UUID | None = None,
) -> ProcessedComplaintResult:
    """
    Unified pipeline to process an incoming complaint:
    1. Redact PII to get safe_text and sensitive entities.
    2. Classify and extract business entities from the safe_text.
    3. Generate vector embeddings of the safe_text.
    4. Find similar complaints using the pre-computed embedding and business entities.
    """
    if complaint_id is None:
        complaint_id = uuid.uuid4()

    # 1. PII Redaction
    safe_text, sensitive_entities = pii_redactor.redact(text)

    # 2. AI Classification & Business Entity Extraction (uses safe_text directly to avoid double redaction)
    classification = await classify_complaint(text, channel, image_base64, safe_text=safe_text)

    # 3. Generate Embedding (using safe_text for PII protection)
    embedding = await generate_embedding(safe_text)

    # 4. Find Similar Complaints (passes embedding and entities directly to avoid DB roundtrips)
    similar_complaints = []
    if embedding:
        similar_complaints = await find_similar(
            complaint_id=complaint_id,
            db=db,
            source_embedding=embedding,
            source_entities=classification.entities,
        )

    return ProcessedComplaintResult(
        complaint_id=complaint_id,
        safe_text=safe_text,
        sensitive_entities=sensitive_entities,
        classification=classification,
        embedding=embedding,
        similar_complaints=similar_complaints,
    )
