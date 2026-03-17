"""
Mocking strategy for POST /summarize (OpenRouter integration):

- We patch httpx.Client in app.main so that no real HTTP calls are made. When
  the endpoint enters "with httpx.Client(...) as client" and calls client.post(...),
  the mock returns a fake response object with .raise_for_status() and .json()
  returning a dict in OpenRouter shape: {"choices": [{"message": {"content": "..."}}]}.

- Patch target: "app.main.httpx.Client" so only the code under test uses the mock;
  TestClient and other code are unchanged.

- Success cases: the mock response's .json() returns a minimal OpenRouter payload.
  We control "content" to test truncation (many words → endpoint truncates,
  truncated=True) or no truncation (few words → truncated=False). We assert
  response schema (summary, model, truncated) and status 200.

- Missing API key: we patch app.main.OPENROUTER_API_KEY to "" so the endpoint
  raises 500 before any HTTP call. No need to mock httpx for this test.

- Upstream failure: we make the mock client.post raise httpx.HTTPError (or
  return a response whose raise_for_status() raises), then assert 503 and
  that the detail mentions the failure.

- All tests use FastAPI TestClient; no real network calls occur.

Authentication coverage:
- Missing Authorization header → HTTP 401 (test_summarize_missing_auth_returns_401).
- Invalid token → HTTP 401 (test_summarize_invalid_auth_returns_401).
- All success and non-auth-failure tests send Authorization: Bearer dev-token.
"""
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_openrouter_response(content: str):
    """build a mock response whose .json() returns OpenRouter-style payload."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {
        "choices": [{"message": {"content": content}}],
    }
    return resp


@patch("app.main.httpx.Client")
def test_summarize_valid_with_truncation(mock_client_cls):
    """valid request; mock returns many words → endpoint truncates to max_length, truncated=True."""
    mock_client_cls.return_value.__enter__.return_value.post.return_value = (
        _mock_openrouter_response("One two three four five six seven eight nine ten")
    )
    response = client.post(
        "/summarize",
        json={
            "text": "One two three four five six seven eight nine ten.",
            "max_length": 5,
        },
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "One two three four five"
    assert data["model"]  # set from OPENROUTER_MODEL (or fallback)
    assert data["truncated"] is True
    assert "summary" in data and "model" in data and "truncated" in data
    assert isinstance(data["summary"], str)
    assert isinstance(data["model"], str)
    assert isinstance(data["truncated"], bool)


@patch("app.main.httpx.Client")
def test_summarize_valid_without_truncation(mock_client_cls):
    """valid request; mock returns few words → no truncation, truncated=False."""
    mock_client_cls.return_value.__enter__.return_value.post.return_value = (
        _mock_openrouter_response("Short text.")
    )
    response = client.post(
        "/summarize",
        json={
            "text": "Short text.",
            "max_length": 10,
        },
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Short text."
    assert data["model"]
    assert data["truncated"] is False
    assert "summary" in data and "model" in data and "truncated" in data


def test_summarize_empty_text_rejected():
    """empty text → 422 validation error."""
    response = client.post(
        "/summarize",
        json={"text": "", "max_length": 100},
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 422


def test_summarize_missing_text_rejected():
    """missing text in body → 422 validation error."""
    response = client.post(
        "/summarize",
        json={"max_length": 100},
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 422


@patch("app.main.OPENROUTER_API_KEY", "")
def test_summarize_missing_api_key_returns_500():
    """OPENROUTER_API_KEY not set → 500, no HTTP call."""
    response = client.post(
        "/summarize",
        json={"text": "Hello world.", "max_length": 10},
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "OPENROUTER_API_KEY" in data["detail"]


@patch("app.main.httpx.Client")
def test_summarize_upstream_failure_returns_503(mock_client_cls):
    """upstream request raises → 503."""
    mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
        httpx.ConnectError("connection error")
    )
    response = client.post(
        "/summarize",
        json={"text": "Hello world.", "max_length": 10},
        headers={"Authorization": "Bearer dev-token"},
    )
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data


def test_summarize_missing_auth_returns_401():
    """missing Authorization header → 401 with clear JSON error."""
    response = client.post(
        "/summarize",
        json={"text": "Hello world.", "max_length": 10},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)


def test_summarize_invalid_auth_returns_401():
    """invalid token → 401 with clear JSON error."""
    response = client.post(
        "/summarize",
        json={"text": "Hello world.", "max_length": 10},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], str)
