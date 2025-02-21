"""
Authentication utilities for the VNC Agent Runner.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from .config import settings

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with the given data and expiration.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

async def verify_api_key(api_key: str = Depends(api_key_header)) -> bool:
    """
    Verify the API key against the configured key.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key missing"
        )
    
    if api_key != settings.VNC_AGENT_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> dict:
    """
    Verify the JWT token and return its payload.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials missing"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=403,
            detail="Invalid authentication credentials"
        )

# Dependency for endpoints that require either API key or JWT
async def verify_auth(
    api_key: str = Depends(api_key_header),
    token: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> bool:
    """
    Verify either API key or JWT token.
    """
    # Try API key first
    if api_key:
        return await verify_api_key(api_key)
    
    # Fall back to JWT
    if token:
        await verify_jwt_token(token)
        return True
    
    raise HTTPException(
        status_code=401,
        detail="Authentication required"
    ) 