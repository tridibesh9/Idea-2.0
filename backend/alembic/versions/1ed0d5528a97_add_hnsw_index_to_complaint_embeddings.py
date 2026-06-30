"""Add HNSW index to complaint embeddings

Revision ID: 1ed0d5528a97
Revises: a27691e4b122
Create Date: 2026-07-01 04:00:18.669311

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '1ed0d5528a97'
down_revision: Union[str, None] = 'a27691e4b122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS complaint_embeddings_embedding_idx ON complaint_embeddings USING hnsw (embedding vector_cosine_ops);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS complaint_embeddings_embedding_idx;")
