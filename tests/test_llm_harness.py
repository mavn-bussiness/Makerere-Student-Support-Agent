import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path
from google.genai import types

from src.main import app
from src.core.llm_harness import TRACE_FILE_PATH

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_trace_file():
    """Ensure trace file is clean before each test."""
    if TRACE_FILE_PATH.exists():
        TRACE_FILE_PATH.unlink()
    yield
    if TRACE_FILE_PATH.exists():
        TRACE_FILE_PATH.unlink()

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")

def test_execute_schema_validation():
    """Test that the endpoint requires a query field."""
    # Missing query
    response = client.post("/api/v1/llm/execute", json={"session_id": "123"})
    assert response.status_code == 422
    
    # Invalid type
    response = client.post("/api/v1/llm/execute", json={"query": {"not": "a string"}})
    assert response.status_code == 422

@patch("src.core.llm_harness.genai.Client")
def test_execute_success_and_trace_logging(mock_client_class):
    """Test successful execution, latency tracking, token extraction, and JSONL logging."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    # Mock the Gemini GenerateContentResponse
    mock_response = MagicMock()
    mock_response.text = "Hello, world!"
    
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 5
    mock_response.usage_metadata = mock_usage
    
    mock_instance.models.generate_content.return_value = mock_response

    payload = {"query": "Say hello", "session_id": "test-session"}
    response = client.post("/api/v1/llm/execute", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["raw_output"] == "Hello, world!"
    assert data["prompt_tokens"] == 10
    assert data["completion_tokens"] == 5
    assert "latency_ms" in data
    assert data["latency_ms"] > 0
    
    # Verify the JSONL trace log
    assert TRACE_FILE_PATH.exists()
    with open(TRACE_FILE_PATH, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        trace = json.loads(lines[0])
        
        assert trace["query"] == "Say hello"
        assert trace["raw_output"] == "Hello, world!"
        assert trace["session_id"] == "test-session"
        assert trace["prompt_tokens"] == 10

@patch("src.core.llm_harness.genai.Client")
def test_execute_provider_error(mock_client_class):
    """Test that provider errors are caught and return a 502 Bad Gateway."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    
    # Simulate a provider API exception (e.g. timeout or auth error)
    mock_instance.models.generate_content.side_effect = Exception("API Timeout")
    
    payload = {"query": "Will timeout"}
    response = client.post("/api/v1/llm/execute", json=payload)
    
    assert response.status_code == 502
    assert response.json()["detail"] == "LLM Provider API Error"
