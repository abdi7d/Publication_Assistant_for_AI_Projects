#!/usr/bin/env python3
"""Test FastAPI routes directly."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a minimal FastAPI app to test routing
app = FastAPI()


@app.get("/")
def index():
    return {"message": "INDEX"}


@app.get("/health")
def health():
    return {"message": "HEALTH"}


@app.get("/testpage")
def testpage():
    return {"message": "TESTPAGE"}


@app.get("/test.html")
def test_html():
    return {"message": "TEST HTML"}


if __name__ == "__main__":
    # Use FastAPI's TestClient
    client = TestClient(app)
    paths = ["/", "/health", "/testpage", "/test.html"]

    print("Testing routes with FastAPI TestClient:")
    print("=" * 70)
    for path in paths:
        resp = client.get(path)
        print(f"{path:20} -> {resp.status_code}: {resp.json()}")
    print("=" * 70)
