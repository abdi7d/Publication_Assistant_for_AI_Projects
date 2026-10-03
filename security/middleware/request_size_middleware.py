# security/middleware/request_size_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable
import logging

from ..configs.config_loader import settings

logger = logging.getLogger(__name__)


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to validate request body sizes before processing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip size checks for GET requests and health endpoints
        if request.method == "GET" or request.url.path in ["/health", "/ready", "/live"]:
            return await call_next(request)
        
        # Check content-length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > settings.MAX_UPLOAD_BYTES:
                    logger.warning(
                        "Request too large: %s bytes (max: %s)",
                        size,
                        settings.MAX_UPLOAD_BYTES
                    )
                    return Response(
                        content=f"Request body too large. Maximum allowed size is {settings.MAX_UPLOAD_BYTES} bytes.",
                        status_code=413
                    )
            except ValueError:
                logger.warning("Invalid content-length header: %s", content_length)
        
        # For requests without content-length, we'll check during body processing
        # by reading the body and checking size
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception("Request processing error: %s", exc)
            raise


__all__ = ["RequestSizeMiddleware"]