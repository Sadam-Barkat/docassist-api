# backend/app/utils/jwt_handler.py
import jwt
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

# Default values for reset token
RESET_TOKEN_EXPIRE_MINUTES = 15

def create_access_token(data: dict, expires_delta: int = JWT_EXPIRE_MINUTES) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_reset_token(data: dict, expires_minutes: int = RESET_TOKEN_EXPIRE_MINUTES) -> str:
    """Create a JWT reset token for password reset"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire, "type": "reset"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str, expected_type: str = "access") -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != expected_type:
            raise PyJWTError("Invalid token type")
        return payload
    except PyJWTError:
        raise

def decode_access_token(token: str) -> dict:
    """Decode JWT access token and return payload (backward compatibility)"""
    return verify_token(token, "access")