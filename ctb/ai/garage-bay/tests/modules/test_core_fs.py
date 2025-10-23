"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/garage-bay
Barton ID: 03.01.02
Unique ID: CTB-8B528782
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
"""

import pytest
from fastapi.testclient import TestClient
from services.mcp.modules.core.fs import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_fs_read_file_not_found():
    """Test reading a non-existent file"""
    response = client.post("/tools/fs/read", json={"path": "/nonexistent/file.txt"})
    assert response.status_code == 404

def test_fs_write_creates_file(tmp_path):
    """Test writing content to a file"""
    test_file = tmp_path / "test.txt"
    response = client.post("/tools/fs/write", json={
        "path": str(test_file),
        "content": "test content"
    })
    assert response.status_code == 200
    assert response.json()["bytes_written"] == len("test content")