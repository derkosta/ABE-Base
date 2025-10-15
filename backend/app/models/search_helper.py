"""
Search helper model for enhanced search capabilities
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TSVECTOR
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class SearchHelper(Base):
    __tablename__ = "search_helpers"

    doc_id = Column(String(255), primary_key=True)  # Paperless document ID
    title = Column(Text, nullable=False)
    normalized_text = Column(TSVECTOR, nullable=True)  # Full-text search vector
    enumbers = Column(ARRAY(String), default=[], nullable=False)  # Extracted E-numbers
    normalized_title = Column(Text, nullable=True)  # Normalized for trigram search
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_search_helpers_normalized_text', 'normalized_text', postgresql_using='gin'),
        Index('ix_search_helpers_enumbers', 'enumbers', postgresql_using='gin'),
        Index('ix_search_helpers_normalized_title', 'normalized_title', postgresql_using='gin'),
        Index('ix_search_helpers_last_seen', 'last_seen_at'),
    )
    
    def __repr__(self):
        return f"<SearchHelper(doc_id='{self.doc_id}', title='{self.title[:50]}...')>"
