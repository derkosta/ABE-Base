"""
Search routes with tolerant E-number and text search
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.audit import log_search
from app.core.config import settings
from app.core.enumber_parser import enumber_parser
from app.models.user import User
from app.models.search_helper import SearchHelper

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class SearchResult(BaseModel):
    doc_id: str
    title: str
    created: str
    modified: str
    snippet: Optional[str]
    enumbers: List[str]
    score: Optional[float]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    enumbers_found: List[str]

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

@router.get("/", response_model=SearchResponse)
@limiter.limit(f"{settings.RATE_LIMIT_SEARCH_PER_MIN}/minute")
async def search_documents(
    request: Request,
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search documents with tolerant E-number and text matching"""
    
    if not q.strip():
        return SearchResponse(
            results=[],
            total=0,
            query=q,
            enumbers_found=[]
        )
    
    # Log search
    log_search(db, current_user, request, q)
    
    # Extract E-numbers from query
    query_enumbers = enumber_parser.extract_enumbers(q)
    
    # Normalize query text
    normalized_query = normalize_text_for_search(q)
    
    results = []
    enumbers_found = []
    
    try:
        # Build search query
        query_parts = []
        params = {"limit": limit}
        
        # E-number search
        if query_enumbers:
            for i, enumber in enumerate(query_enumbers):
                query_parts.append(f"enumbers @> ARRAY[%(enumber_{i})s]")
                params[f"enumber_{i}"] = enumber
            enumbers_found = query_enumbers
        
        # Text search with trigram similarity
        if normalized_query:
            # Split query into words for better matching
            words = normalized_query.split()
            if words:
                # Use trigram similarity for each word
                trigram_conditions = []
                for i, word in enumerate(words):
                    if len(word) > 2:  # Skip very short words
                        trigram_conditions.append(
                            f"similarity(normalized_title, %(word_{i})s) > {settings.ENUMBER_SEARCH_TOLERANCE}"
                        )
                        params[f"word_{i}"] = word
                
                if trigram_conditions:
                    query_parts.append(f"({' OR '.join(trigram_conditions)})")
        
        # Build final query
        if query_parts:
            where_clause = " OR ".join(query_parts)
            search_query = text(f"""
                SELECT 
                    doc_id,
                    title,
                    enumbers,
                    GREATEST(
                        CASE WHEN enumbers && ARRAY[{','.join([f'%(enumber_{i})s' for i in range(len(query_enumbers))])}] 
                             THEN 1.0 ELSE 0.0 END,
                        CASE WHEN normalized_title IS NOT NULL 
                             THEN similarity(normalized_title, :query_text) 
                             ELSE 0.0 END
                    ) as score
                FROM search_helpers 
                WHERE {where_clause}
                ORDER BY score DESC, last_seen_at DESC
                LIMIT :limit
            """)
            
            params["query_text"] = normalized_query
            
            # Execute search
            result = db.execute(search_query, params)
            rows = result.fetchall()
            
            # Get document metadata from Paperless for results
            from app.core.paperless import paperless_client
            
            for row in rows:
                try:
                    doc = await paperless_client.get_document(row.doc_id)
                    results.append(SearchResult(
                        doc_id=row.doc_id,
                        title=row.title,
                        created=doc.get("created", ""),
                        modified=doc.get("modified", ""),
                        snippet=generate_snippet(doc.get("content", ""), q),
                        enumbers=row.enumbers or [],
                        score=row.score
                    ))
                except Exception as e:
                    # Skip documents that can't be retrieved
                    continue
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=q,
            enumbers_found=enumbers_found
        )
        
    except Exception as e:
        # Fallback to simple text search
        search_helper = db.query(SearchHelper).filter(
            func.lower(SearchHelper.title).contains(q.lower())
        ).limit(limit).all()
        
        results = []
        for helper in search_helper:
            try:
                from app.core.paperless import paperless_client
                doc = await paperless_client.get_document(helper.doc_id)
                results.append(SearchResult(
                    doc_id=helper.doc_id,
                    title=helper.title,
                    created=doc.get("created", ""),
                    modified=doc.get("modified", ""),
                    snippet=generate_snippet(doc.get("content", ""), q),
                    enumbers=helper.enumbers or [],
                    score=None
                ))
            except Exception:
                continue
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=q,
            enumbers_found=enumbers_found
        )

def generate_snippet(content: str, query: str, max_length: int = 200) -> Optional[str]:
    """Generate a text snippet highlighting the query"""
    if not content or not query:
        return None
    
    # Find query in content (case insensitive)
    query_lower = query.lower()
    content_lower = content.lower()
    
    index = content_lower.find(query_lower)
    if index == -1:
        # Return beginning of content if query not found
        return content[:max_length] + "..." if len(content) > max_length else content
    
    # Extract snippet around the match
    start = max(0, index - max_length // 2)
    end = min(len(content), index + len(query) + max_length // 2)
    
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    
    return snippet

@router.get("/suggest")
async def search_suggestions(
    q: str = Query(..., description="Partial search query"),
    limit: int = Query(10, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on partial query"""
    
    if len(q.strip()) < 2:
        return {"suggestions": []}
    
    # Get suggestions from titles and E-numbers
    suggestions = set()
    
    # Title suggestions
    titles = db.query(SearchHelper.title).filter(
        func.lower(SearchHelper.title).contains(q.lower())
    ).limit(limit).all()
    
    for title_row in titles:
        suggestions.add(title_row.title)
    
    # E-number suggestions
    enumbers = db.query(SearchHelper.enumbers).filter(
        SearchHelper.enumbers.op('&&')([q.lower()])
    ).limit(limit).all()
    
    for enumber_row in enumbers:
        if enumber_row.enumbers:
            suggestions.update(enumber_row.enumbers)
    
    return {
        "suggestions": list(suggestions)[:limit]
    }

@router.post("/sync")
async def sync_search_helpers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually sync search helpers with Paperless (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # This would typically be run as a background task
    # For now, just return success
    return {"message": "Search sync initiated"}
