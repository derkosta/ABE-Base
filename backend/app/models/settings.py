"""
Application settings model
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base

class Settings(Base):
    __tablename__ = "settings"

    id = Column(String(50), primary_key=True, default="singleton")
    paperless_base_url = Column(String(500), nullable=True)
    paperless_api_token = Column(Text, nullable=True)
    allow_self_signup = Column(Boolean, default=False, nullable=False)
    max_upload_mb = Column(String(10), default="50", nullable=False)
    session_timeout_hours = Column(String(5), default="24", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Settings(id='{self.id}')>"
