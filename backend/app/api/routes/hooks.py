"""
n8n API hooks for external integration
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

class HookSearchRequest(BaseModel):
    query: Optional[str] = None
    model: Optional[str] = None
    eNumber: Optional[str] = None
    limit: int = 10

class HookSearchResult(BaseModel):
    docId: str
    title: str
    snippet: Optional[str]
    downloadUrl: str
    enumbers: List[str]

class HookSearchResponse(BaseModel):
    results: List[HookSearchResult]
    total: int
    query: str

@router.post("/search", response_model=HookSearchResponse)
async def hook_search(
    request: HookSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """n8n API hook for programmatic document search"""
    
    # Build search query from request parameters
    query_parts = []
    
    if request.query:
        query_parts.append(request.query)
    
    if request.model:
        query_parts.append(request.model)
    
    if request.eNumber:
        query_parts.append(request.eNumber)
    
    search_query = " ".join(query_parts)
    
    if not search_query.strip():
        return HookSearchResponse(
            results=[],
            total=0,
            query=""
        )
    
    # Use the same search logic as the main search endpoint
    from app.api.routes.search import search_documents
    from fastapi import Request
    
    # Create a mock request for the search function
    class MockRequest:
        def __init__(self):
            self.headers = {}
    
    mock_request = MockRequest()
    
    # Get search results
    search_response = await search_documents(
        request=mock_request,
        q=search_query,
        limit=request.limit,
        current_user=current_user,
        db=db
    )
    
    # Transform results to hook format
    results = []
    for result in search_response.results:
        results.append(HookSearchResult(
            docId=result.doc_id,
            title=result.title,
            snippet=result.snippet,
            downloadUrl=f"/api/docs/{result.doc_id}/download",
            enumbers=result.enumbers
        ))
    
    return HookSearchResponse(
        results=results,
        total=len(results),
        query=search_query
    )

@router.get("/doc/{doc_id}/meta")
async def get_document_meta(
    doc_id: str,
    limit: int = Query(10, description="Number of recent audits to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document metadata and recent audits for n8n"""
    
    try:
        from app.core.paperless import paperless_client
        
        # Get document metadata
        doc = await paperless_client.get_document(doc_id)
        
        # Get recent audits
        from app.models.audit import Audit
        audits = db.query(Audit).filter(
            Audit.doc_id == doc_id
        ).order_by(Audit.created_at.desc()).limit(limit).all()
        
        audit_data = []
        for audit in audits:
            audit_data.append({
                "user": audit.user.username,
                "action": audit.action.value,
                "created_at": audit.created_at.isoformat(),
                "ip_address": audit.ip_address
            })
        
        return {
            "document": {
                "id": doc.get("id"),
                "title": doc.get("title"),
                "created": doc.get("created"),
                "modified": doc.get("modified"),
                "correspondent": doc.get("correspondent", {}).get("name") if doc.get("correspondent") else None,
                "tags": [tag.get("name", "") for tag in doc.get("tags", [])],
                "download_url": f"/api/docs/{doc_id}/download"
            },
            "recent_audits": audit_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

@router.get("/health")
async def hook_health_check():
    """Health check endpoint for n8n monitoring"""
    return {
        "status": "healthy",
        "service": "abe-portal-hooks",
        "version": "1.0.0"
    }
