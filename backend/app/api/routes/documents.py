"""
Document management routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import io
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.paperless import paperless_client
from app.core.audit import log_upload, log_download
from app.models.user import User
from app.models.search_helper import SearchHelper
from app.core.enumber_parser import enumber_parser
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class DocumentResponse(BaseModel):
    id: str
    title: str
    created: str
    modified: str
    content: Optional[str]
    tags: list
    correspondent: Optional[str]
    document_type: Optional[str]

class DocumentListResponse(BaseModel):
    id: str
    title: str
    created: str
    modified: str
    tags: list
    correspondent: Optional[str]

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload document to Paperless"""
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_MB}MB"
        )
    
    try:
        # Upload to Paperless
        result = await paperless_client.upload_document(
            file_content=file_content,
            filename=file.filename or "document.pdf",
            title=title or file.filename or "Uploaded Document"
        )
        
        doc_id = str(result.get("id"))
        doc_title = result.get("title", "Unknown Document")
        
        # Log upload
        log_upload(db, current_user, request, doc_id, doc_title)
        
        # Trigger search helper update (async)
        await update_search_helpers(db, doc_id)
        
        return {
            "message": "Document uploaded successfully",
            "document": {
                "id": doc_id,
                "title": doc_title,
                "created": result.get("created"),
                "modified": result.get("modified")
            }
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document metadata"""
    try:
        doc = await paperless_client.get_document(doc_id)
        
        return DocumentResponse(
            id=str(doc.get("id")),
            title=doc.get("title", ""),
            created=doc.get("created", ""),
            modified=doc.get("modified", ""),
            content=doc.get("content", ""),
            tags=[tag.get("name", "") for tag in doc.get("tags", [])],
            correspondent=doc.get("correspondent", {}).get("name") if doc.get("correspondent") else None,
            document_type=doc.get("document_type", {}).get("name") if doc.get("document_type") else None
        )
        
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download document with audit logging"""
    try:
        # Get document metadata first for logging
        doc = await paperless_client.get_document(doc_id)
        doc_title = doc.get("title", "Unknown Document")
        
        # Download document content
        content = await paperless_client.download_document(doc_id)
        
        # Log download
        log_download(db, current_user, request, doc_id, doc_title)
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={doc_title}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Download failed for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or download failed"
        )

@router.get("/{doc_id}/thumb")
async def get_document_thumbnail(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get document thumbnail"""
    try:
        thumb_content = await paperless_client.get_document_thumb(doc_id)
        
        if not thumb_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thumbnail not available"
            )
        
        return StreamingResponse(
            io.BytesIO(thumb_content),
            media_type="image/jpeg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thumbnail failed for document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not available"
        )

@router.get("/{doc_id}/audit")
async def get_document_audit(
    doc_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit trail for a document"""
    from app.models.audit import Audit, AuditAction
    
    audits = db.query(Audit).filter(
        Audit.doc_id == doc_id
    ).order_by(Audit.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": str(audit.id),
            "user": audit.user.username,
            "action": audit.action.value,
            "created_at": audit.created_at.isoformat(),
            "ip_address": audit.ip_address,
            "user_agent": audit.user_agent
        }
        for audit in audits
    ]

async def update_search_helpers(db: Session, doc_id: str):
    """Update search helpers for a document"""
    try:
        # Get document content from Paperless
        content = await paperless_client.get_document_content(doc_id)
        doc = await paperless_client.get_document(doc_id)
        
        if not content and not doc:
            return
        
        title = doc.get("title", "") if doc else ""
        full_text = f"{title} {content}" if content else title
        
        # Extract E-numbers
        enumbers = enumber_parser.extract_enumbers(full_text)
        
        # Normalize title for trigram search
        normalized_title = normalize_text_for_search(title)
        
        # Create or update search helper
        search_helper = db.query(SearchHelper).filter(
            SearchHelper.doc_id == doc_id
        ).first()
        
        if not search_helper:
            search_helper = SearchHelper(doc_id=doc_id)
            db.add(search_helper)
        
        search_helper.title = title
        search_helper.enumbers = enumbers
        search_helper.normalized_title = normalized_title
        search_helper.normalized_text = full_text  # In production, use proper TSVECTOR
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to update search helpers for {doc_id}: {e}")
        db.rollback()

def normalize_text_for_search(text: str) -> str:
    """Normalize text for trigram search"""
    if not text:
        return ""
    
    import re
    import unicodedata
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
