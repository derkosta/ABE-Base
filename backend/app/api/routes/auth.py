"""
Authentication routes
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_password_hash
)
from app.core.audit import log_login
from app.models.user import User, UserRole

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserInfo(BaseModel):
    id: str
    username: str
    email: str | None
    role: str
    is_active: bool

@router.post("/login", response_model=LoginResponse)
@limiter.limit(f"{settings.RATE_LIMIT_LOGIN_PER_MIN}/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    response: Response = None
):
    """Authenticate user and return JWT token"""
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Log login
    log_login(db, user, request)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set httpOnly cookie for web frontend
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=not settings.DEBUG,  # Use secure cookies in production
        samesite="lax"
    )
    
    return LoginResponse(
        access_token=access_token,
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active
        }
    )

@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie"""
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active
    )

@router.get("/setup-status")
async def setup_status(db: Session = Depends(get_db)):
    """Check if initial setup is needed"""
    user_count = db.query(User).count()
    return {
        "setup_required": user_count == 0,
        "user_count": user_count
    }

@router.post("/setup")
async def initial_setup(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    response: Response = None
):
    """Create initial admin user (only when no users exist)"""
    user_count = db.query(User).count()
    
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup already completed"
        )
    
    # Create admin user
    admin_user = User(
        username=login_data.username,
        password_hash=get_password_hash(login_data.password),
        role=UserRole.ADMIN,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Log setup
    log_login(db, admin_user, request)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin_user.username}, expires_delta=access_token_expires
    )
    
    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    return {
        "message": "Setup completed successfully",
        "access_token": access_token,
        "user": {
            "id": str(admin_user.id),
            "username": admin_user.username,
            "role": admin_user.role.value
        }
    }
