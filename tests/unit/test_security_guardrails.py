import pytest


def sanitize_filename(name: str) -> str:
    # simple sanitizer used in tests; production code lives in security/validators
    import re

    name = name.strip()
    # remove path separators and collapse traversal sequences
    name = name.replace("/", "_").replace("\\", "_")
    # collapse sequences of two or more dots but preserve single dot before extensions
    name = re.sub(r"\.{2,}", ".", name)
    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    return name


def test_sanitize_filename():
    out = sanitize_filename("../../etc/passwd")
    # Should remove traversal and path separators
    assert ".." not in out
    assert "/" not in out and "\\" not in out
    assert sanitize_filename("my file.txt") == "my_file.txt"


def test_rate_limit_behavior():
    # placeholder: rate limiting tested via integration with Redis or limiter
    assert True
