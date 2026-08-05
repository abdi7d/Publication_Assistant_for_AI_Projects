# security/middleware/security_headers_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable
import logging

from ..configs.config_loader import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # HTTPS enforcement in production (before processing request)
        if settings.APP_ENV == "production":
            if request.url.scheme != "https":
                # Redirect to HTTPS
                https_url = request.url.replace(scheme="https")
                logger.warning(
                    "Redirecting HTTP to HTTPS: %s -> %s", request.url, https_url)
                return Response(
                    status_code=301,
                    headers={"Location": str(https_url)}
                )

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Only add HSTS in production
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if settings.APP_ENV != "production":
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com;"
            )
        else:
            csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"

        response.headers["Content-Security-Policy"] = csp
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


__all__ = ["SecurityHeadersMiddleware"]
