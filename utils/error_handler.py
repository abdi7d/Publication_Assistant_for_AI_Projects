# utils/error_handler.py
"""
Centralized error handling for the application.
Provides consistent error responses and logging.
"""
from typing import Any, Dict, Optional
import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Base exception for application-specific errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(ApplicationError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message, status_code=404)


class ExternalServiceError(ApplicationError):
    """Raised when an external service call fails."""
    
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"External service '{service_name}' failed"
        super().__init__(message, status_code=503, details=details)


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle application-specific errors."""
    logger.error(
        "Application error: %s",
        exc.message,
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details if exc.details else None,
        }
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error: %s",
        str(exc),
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "status_code": 422,
            "details": exc.errors(),
        }
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP error: %s",
        exc.detail,
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.exception(
        "Unexpected error: %s",
        str(exc),
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
        }
    )


def setup_error_handlers(app):
    """Register error handlers with FastAPI app."""
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)


__all__ = [
    "ApplicationError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceNotFoundError",
    "ExternalServiceError",
    "setup_error_handlers",
]