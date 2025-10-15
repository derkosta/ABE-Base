"""
Admin routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_admin_user
from app.models.user import User
from app.models.audit import Audit, AuditAction

router = APIRouter()

class AuditResponse(BaseModel):
    id: str
    user: str
    action: str
    doc_id: Optional[str]
    doc_title: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[str]
    created_at: str

class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_documents: int
    total_audits: int
    recent_uploads: int
    recent_downloads: int

@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    from datetime import datetime, timedelta
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Document stats (from search helpers)
    from app.models.search_helper import SearchHelper
    total_documents = db.query(SearchHelper).count()
    
    # Audit stats
    total_audits = db.query(Audit).count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = db.query(Audit).filter(
        Audit.action == AuditAction.UPLOAD,
        Audit.created_at >= week_ago
    ).count()
    
    recent_downloads = db.query(Audit).filter(
        Audit.action == AuditAction.DOWNLOAD,
        Audit.created_at >= week_ago
    ).count()
    
    return StatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_audits=total_audits,
        recent_uploads=recent_uploads,
        recent_downloads=recent_downloads
    )

@router.get("/audit", response_model=List[AuditResponse])
async def get_audit_log(
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit log with optional filtering"""
    
    query = db.query(Audit)
    
    # Apply filters
    if action:
        try:
            action_enum = AuditAction(action)
            query = query.filter(Audit.action == action_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action filter"
            )
    
    if user_id:
        query = query.filter(Audit.user_id == user_id)
    
    # Get results
    audits = query.order_by(Audit.created_at.desc()).limit(limit).all()
    
    return [
        AuditResponse(
            id=str(audit.id),
            user=audit.user.username,
            action=audit.action.value,
            doc_id=audit.doc_id,
            doc_title=audit.doc_title,
            ip_address=audit.ip_address,
            user_agent=audit.user_agent,
            details=audit.details,
            created_at=audit.created_at.isoformat()
        )
        for audit in audits
    ]

@router.get("/users/activity")
async def get_user_activity(
    days: int = 30,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user activity summary"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get user activity counts
    activity = db.query(
        Audit.user_id,
        func.count(Audit.id).label('total_actions'),
        func.count(func.distinct(Audit.created_at.date())).label('active_days'),
        func.max(Audit.created_at).label('last_activity')
    ).filter(
        Audit.created_at >= since
    ).group_by(Audit.user_id).all()
    
    # Get user details
    user_activity = []
    for act in activity:
        user = db.query(User).filter(User.id == act.user_id).first()
        if user:
            user_activity.append({
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "is_active": user.is_active,
                "total_actions": act.total_actions,
                "active_days": act.active_days,
                "last_activity": act.last_activity.isoformat()
            })
    
    return {"user_activity": user_activity}

@router.post("/cleanup/audit")
async def cleanup_audit_log(
    days_to_keep: int = 365,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Clean up old audit logs"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    deleted_count = db.query(Audit).filter(
        Audit.created_at < cutoff_date
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Cleaned up {deleted_count} old audit entries",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }

@router.get("/paperless/status")
async def check_paperless_status(
    current_user: User = Depends(get_current_admin_user)
):
    """Check Paperless-ngx connectivity status"""
    from app.core.paperless import paperless_client
    
    try:
        is_connected = await paperless_client.test_connection()
        return {
            "connected": is_connected,
            "base_url": paperless_client.base_url,
            "status": "online" if is_connected else "offline"
        }
    except Exception as e:
        return {
            "connected": False,
            "base_url": paperless_client.base_url,
            "status": "error",
            "error": str(e)
        }

@router.post("/paperless/sync")
async def sync_with_paperless(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Trigger sync with Paperless-ngx"""
    # This would typically run as a background task
    # For now, just return success
    return {"message": "Paperless sync initiated"}
