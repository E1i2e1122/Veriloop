"""
Security utilities for authentication.

This module provides:
- Password hashing with bcrypt
- JWT token creation and validation
- Token payload models
- Configuration constants
"""

import os
import re
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

# Password hashing configuration
BCRYPT_ROUNDS = 12  # Production-grade cost factor
BCRYPT_MAX_PASSWORD_BYTES = 72  # bcrypt only uses the first 72 bytes of a password

# JWT Configuration - load from environment
# REQUIRED: JWT_SECRET_KEY must be set in production
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY environment variable is REQUIRED. Generate a secure key with: openssl rand -hex 32"
    )
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

# Password strength requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True


class TokenPayload(BaseModel):
    """JWT token payload model."""

    sub: str  # user_id
    exp: datetime
    type: str  # "access" or "refresh"
    jti: str | None = None  # Token ID for refresh tokens


def _password_bytes(password: str) -> bytes:
    # Truncate explicitly (as passlib did) so hashes created before the switch keep verifying.
    return password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False  # malformed or non-bcrypt hash


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def create_access_token(user_id: str) -> str:
    """Create a short-lived access token."""
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expires, "type": "access"}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, token_id: str) -> str:
    """Create a long-lived refresh token with unique ID for rotation."""
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expires, "type": "refresh", "jti": token_id}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload | None:
    """
    Decode and validate a JWT token.

    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Check password complexity requirements.

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"

    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


def is_account_locked(locked_until: datetime | None) -> bool:
    """Check if an account is currently locked."""
    if locked_until is None:
        return False
    return locked_until > datetime.utcnow()


def get_lockout_time() -> datetime:
    """Get the lockout expiration time from now."""
    return datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
