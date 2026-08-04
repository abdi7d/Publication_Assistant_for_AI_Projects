# security/middleware/auth_middleware.py
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import logging

from ..configs.config_loader import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """JWT Authentication middleware for FastAPI."""
    
    @staticmethod
    def verify_token(credentials: Optional[HTTPAuthorizationCredentials]) -> dict:
        """Verify JWT token and return payload."""
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as exc:
            logger.warning("JWT verification failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            to_encode.update({"exp": expires_delta})
        else:
            to_encode.update({"exp": settings.ACCESS_TOKEN_EXPIRE_SECONDS})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt


async def require_auth(request: Request) -> dict:
    """Dependency to require authentication for endpoints."""
    credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
    return AuthMiddleware.verify_token(credentials)


def optional_auth(request: Request) -> Optional[dict]:
    """Dependency for optional authentication."""
    credentials: Optional[HTTPAuthorizationCredentials] = request.headers.get("authorization")
    if credentials:
        try:
            return AuthMiddleware.verify_token(credentials)
        except HTTPException:
            return None
    return None


__all__ = ["AuthMiddleware", "require_auth", "optional_auth"]