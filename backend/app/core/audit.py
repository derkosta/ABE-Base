"""
Audit logging utilities
"""
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit import Audit, AuditAction
from app.models.user import User
from app.core.config import settings

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    forwarded = request.headers.get("X-Forwarded")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if hasattr(request.client, "host"):
        return request.client.host
    
    return "unknown"

def get_user_agent(request: Request) -> str:
    """Get user agent from request"""
    return request.headers.get("User-Agent", "unknown")

def log_audit(
    db: Session,
    user: User,
    action: AuditAction,
    request: Request,
    doc_id: Optional[str] = None,
    doc_title: Optional[str] = None,
    details: Optional[str] = None
) -> None:
    """Log an audit entry"""
    audit = Audit(
        user_id=user.id,
        action=action,
        doc_id=doc_id,
        doc_title=doc_title,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details=details
    )
    
    db.add(audit)
    db.commit()

def log_login(db: Session, user: User, request: Request) -> None:
    """Log user login"""
    log_audit(db, user, AuditAction.LOGIN, request)

def log_upload(db: Session, user: User, request: Request, doc_id: str, doc_title: str) -> None:
    """Log document upload"""
    log_audit(db, user, AuditAction.UPLOAD, request, doc_id, doc_title)

def log_download(db: Session, user: User, request: Request, doc_id: str, doc_title: str) -> None:
    """Log document download"""
    log_audit(db, user, AuditAction.DOWNLOAD, request, doc_id, doc_title)

def log_search(db: Session, user: User, request: Request, query: str) -> None:
    """Log search query"""
    log_audit(db, user, AuditAction.SEARCH, request, details=f'query="{query}"')

def log_user_action(
    db: Session, 
    admin_user: User, 
    request: Request, 
    action: AuditAction, 
    target_username: str,
    details: Optional[str] = None
) -> None:
    """Log admin user management action"""
    log_audit(
        db, 
        admin_user, 
        action, 
        request, 
        details=f'target="{target_username}"{f", {details}" if details else ""}'
    )
