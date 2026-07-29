from __future__ import annotations
import os
import re
import mimetypes
from typing import Optional, Tuple

from ..configs.config_loader import settings

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "docx", "png", "jpg", "jpeg"}
ALLOWED_MIMES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
}
SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9_.-]{1,255}$")


def sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename or "")
    if SAFE_FILENAME.match(name):
        return name
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)[:255]


def validate_extension(filename: str) -> Tuple[bool, str]:
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if not ext:
        return False, "no_extension"
    if ext not in ALLOWED_EXTENSIONS:
        return False, "extension_not_allowed"
    return True, "ok"


def validate_mime_type(stream, filename: str) -> Tuple[bool, str]:
    guessed, _ = mimetypes.guess_type(filename)
    if not guessed:
        return False, "unknown_mime"
    if guessed.startswith(("text", "application", "image")):
        return True, "ok"
    return False, "disallowed_mime"


def validate_upload_size(file_bytes: bytes) -> Tuple[bool, str]:
    if len(file_bytes) > settings.MAX_UPLOAD_BYTES:
        return False, "file_too_large"
    return True, "ok"


def validate_upload(file_bytes: bytes, filename: str, mime: Optional[str]) -> Tuple[bool, str]:
    ok, message = validate_extension(filename)
    if not ok:
        return False, message

    ok, message = validate_upload_size(file_bytes)
    if not ok:
        return False, message

    if mime and mime not in ALLOWED_MIMES:
        return False, "mime_type_not_allowed"

    return True, ""


__all__ = [
    "sanitize_filename",
    "validate_extension",
    "validate_mime_type",
    "validate_upload_size",
    "validate_upload",
]
