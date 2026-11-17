"""
Authentication API endpoints.

Provides endpoints for:
- User registration
- User login (with rate limiting and account lockout)
- Token refresh (with rotation)
- Logout (token revocation)
- Current user info
"""

import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session, select

from .db import get_session
from .middleware import auth as auth_settings
from .middleware.auth import get_current_active_user, get_current_user_optional
from .middleware.auth_enforcement import SESSION_COOKIE_NAME
from .middleware.rate_limit import AUTH_LIMITS, limiter
from .models_auth import (
    LoginRequest,
    ProjectMember,
    RefreshToken,
    RefreshTokenRequest,
    TokenResponse,
    User,
    UserCreate,
    UserResponse,
)
from .security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    MAX_FAILED_ATTEMPTS,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_lockout_time,
    hash_password,
    is_account_locked,
    is_password_strong,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Feature flag for registration
ALLOW_REGISTRATION = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"


def _set_session_cookie(response: Response, request: Request, access_token: str) -> None:
    """Mirror the access token into an httpOnly cookie for browser media, downloads, and event streams."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    secure = request.url.scheme == "https" or forwarded_proto.split(",")[0].strip() == "https"
    response.set_cookie(
        SESSION_COOKIE_NAME,
        access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit(AUTH_LIMITS["register"])
async def register(request: Request, data: UserCreate, session: Session = Depends(get_session)):
    """
    Create a new user account.

    Validates email uniqueness and password strength.
    """
    if not ALLOW_REGISTRATION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is currently disabled")

    # Check if email already exists
    existing = session.exec(select(User).where(User.email == data.email.lower())).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Validate password strength
    is_strong, error_message = is_password_strong(data.password)
    if not is_strong:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

    # Create user
    user = User(email=data.email.lower(), password_hash=hash_password(data.password), full_name=data.full_name)
    session.add(user)
    session.commit()
    session.refresh(user)

    # Auto-add user to Default Project with viewer role
    DEFAULT_PROJECT_ID = "default"
    try:
        # Check if default project exists (it should be auto-created on startup)
        from .models_db import Project

        default_project = session.get(Project, DEFAULT_PROJECT_ID)
        if default_project:
            member = ProjectMember(project_id=DEFAULT_PROJECT_ID, user_id=user.id, role="viewer")
            session.add(member)
            session.commit()
            logger.info(f"Added user {user.email} to Default Project")
    except Exception as e:
        # Don't fail registration if project membership fails
        logger.warning(f"Failed to add user to Default Project: {e}")

    logger.info(f"New user registered: {user.email} (id={user.id})")

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_LIMITS["login"])
async def login(request: Request, response: Response, data: LoginRequest, session: Session = Depends(get_session)):
    """
    Authenticate user and return JWT tokens.

    Includes account lockout after repeated failed attempts.
    """
    user = session.exec(select(User).where(User.email == data.email.lower())).first()

    if not user:
        # Use same error message to prevent email enumeration
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Check account lockout
    if is_account_locked(user.locked_until):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail=f"Account locked until {user.locked_until.isoformat()}"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Verify password
    if not verify_password(data.password, user.password_hash):
        user.failed_login_attempts += 1

        # Lock account if too many failed attempts
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = get_lockout_time()
            logger.warning(f"Account locked due to failed attempts: {user.email}")

        session.commit()

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()

    # Create access token
    access_token = create_access_token(user.id)

    # Create and store refresh token
    refresh_token_id = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, refresh_token_id)

    db_refresh_token = RefreshToken(
        id=refresh_token_id,
        user_id=user.id,
        token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
    )
    session.add(db_refresh_token)
    session.commit()

    logger.info(f"User logged in: {user.email}")

    _set_session_cookie(response, request, access_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(AUTH_LIMITS["refresh"])
async def refresh(
    request: Request, response: Response, data: RefreshTokenRequest, session: Session = Depends(get_session)
):
    """
    Refresh access token using refresh token.

    Implements token rotation: old refresh token is revoked
    and a new one is issued.
    """
    token_data = decode_token(data.refresh_token)
    if not token_data or token_data.type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Find the stored token
    token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).where(RefreshToken.revoked_at == None)
    ).first()

    if not db_token:
        # Possible token reuse attack - revoke all user's tokens
        logger.warning(f"Possible token reuse attack for user: {token_data.sub}")

        tokens = session.exec(select(RefreshToken).where(RefreshToken.user_id == token_data.sub)).all()
        for t in tokens:
            t.revoked_at = datetime.utcnow()
        session.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or reused refresh token. All sessions revoked."
        )

    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    # Get user
    user = session.get(User, token_data.sub)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Create new tokens (rotation)
    new_access_token = create_access_token(user.id)
    new_refresh_token_id = str(uuid.uuid4())
    new_refresh_token = create_refresh_token(user.id, new_refresh_token_id)

    # Revoke old token
    db_token.revoked_at = datetime.utcnow()
    db_token.replaced_by = new_refresh_token_id

    # Store new token
    new_db_token = RefreshToken(
        id=new_refresh_token_id,
        user_id=user.id,
        token_hash=hashlib.sha256(new_refresh_token.encode()).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
    )
    session.add(new_db_token)
    session.commit()

    _set_session_cookie(response, request, new_access_token)
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(response: Response, data: RefreshTokenRequest, session: Session = Depends(get_session)):
    """
    Revoke the refresh token (logout).

    The access token will naturally expire, but the refresh
    token is immediately invalidated.
    """
    token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    db_token = session.exec(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()

    if db_token and db_token.revoked_at is None:
        db_token.revoked_at = datetime.utcnow()
        session.commit()
        logger.info(f"User logged out: user_id={db_token.user_id}")

    _clear_session_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/status")
async def auth_status(current_user: User | None = Depends(get_current_user_optional)):
    """
    Report whether authentication is enforced and whether the caller is authenticated.

    Public endpoint used by server-side frontend routes (e.g. the AI assistant) to
    reject anonymous callers before spending LLM tokens.
    """
    return {
        "require_auth": auth_settings.REQUIRE_AUTH,
        "authenticated": current_user is not None,
        "user_id": current_user.id if current_user else None,
        "is_superuser": bool(current_user and current_user.is_superuser),
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user's information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user), session: Session = Depends(get_session)
):
    """
    Revoke all refresh tokens for the current user.

    Use this to log out from all devices/sessions.
    """
    tokens = session.exec(
        select(RefreshToken).where(RefreshToken.user_id == current_user.id).where(RefreshToken.revoked_at == None)
    ).all()

    count = 0
    for token in tokens:
        token.revoked_at = datetime.utcnow()
        count += 1

    session.commit()

    logger.info(f"Revoked {count} tokens for user: {current_user.email}")

    return {"message": f"Logged out from {count} session(s)"}
