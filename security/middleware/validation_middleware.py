from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from typing import Callable
from ..validators.input_validators import validate_prompt
import json


class ValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only validate JSON bodies for known endpoints
        if request.method in ("POST", "PUT", "PATCH") and request.headers.get("content-type", "").startswith("application/json"):
            body_bytes = await request.body()
            if body_bytes:
                try:
                    payload = json.loads(body_bytes)
                except Exception:
                    return Response(content="Malformed JSON", status_code=400)

                # If payload contains 'prompt' run specialized validation
                prompt = payload.get("prompt") if isinstance(payload, dict) else None
                if prompt is not None:
                    ok, msg = validate_prompt(prompt)
                    if not ok:
                        return Response(content=msg, status_code=422)

        response = await call_next(request)
        return response
from __future__ import annotations
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE, HTTP_400_BAD_REQUEST
from security.validators.validators import sanitize_text, validate_prompt_length, validate_prompt_tokens


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Generic request validation middleware.

    - Enforces a maximum body size
    - Sanitizes top-level `prompt` fields when present
    - Returns standardized error codes
    """

    def __init__(self, app, max_body_bytes: int = 2 * 1024 * 1024):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        body = await request.body()
        if len(body) > self.max_body_bytes:
            return Response(content=json.dumps({"error": "request_too_large"}), status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE, media_type="application/json")

        if request.headers.get("content-type", "").startswith("application/json"):
            try:
                payload = await request.json()
            except Exception:
                return Response(content=json.dumps({"error": "malformed_json"}), status_code=HTTP_400_BAD_REQUEST, media_type="application/json")

            # If a `prompt` or `input` field exists, apply sanitization and basic validation
            for field in ("prompt", "input", "text"):
                if field in payload and isinstance(payload[field], str):
                    payload[field] = sanitize_text(payload[field])
                    ok, reason = validate_prompt_length(payload[field])
                    if not ok:
                        return Response(content=json.dumps({"error": reason}), status_code=HTTP_400_BAD_REQUEST, media_type="application/json")
                    ok, reason = validate_prompt_tokens(payload[field])
                    if not ok:
                        return Response(content=json.dumps({"error": reason}), status_code=HTTP_400_BAD_REQUEST, media_type="application/json")

            # Replace request._body for downstream handlers
            request._body = json.dumps(payload).encode("utf-8")

        return await call_next(request)


__all__ = ["InputValidationMiddleware"]
