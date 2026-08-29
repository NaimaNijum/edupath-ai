"""Tests for Gemini error classification, retry policy, and embed_text."""
from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from google.genai import errors as genai_errors

from app.core.exceptions import LLMError, LLMQuotaError
from app.llm.gemini import (
    GeminiProvider,
    _extract_retry_after_seconds,
    _is_non_retryable_client_error,
    _is_quota_error,
    _is_retryable,
    _is_transient_5xx,
)


def _make_api_error(code: int, status: str | None = None, message: str = "boom", details: object | None = None) -> genai_errors.APIError:
    response = httpx.Response(code, json={"error": {"code": code, "status": status or "", "message": message, "details": details or []}})
    return genai_errors.APIError(code, response.json(), response)


@pytest.fixture
def mock_provider():
    provider = GeminiProvider()
    provider._client = MagicMock()
    return provider


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def test_is_quota_error_detects_429() -> None:
    assert _is_quota_error(_make_api_error(429, "RESOURCE_EXHAUSTED")) is True
    assert _is_quota_error(_make_api_error(429, None, message="quota")) is True


def test_is_quota_error_ignores_other_codes() -> None:
    assert _is_quota_error(_make_api_error(500, "UNAVAILABLE")) is False
    assert _is_quota_error(_make_api_error(404, "NOT_FOUND")) is False


def test_is_transient_5xx() -> None:
    assert _is_transient_5xx(_make_api_error(500)) is True
    assert _is_transient_5xx(_make_api_error(503)) is True
    assert _is_transient_5xx(_make_api_error(429)) is False


def test_is_non_retryable_client_error() -> None:
    assert _is_non_retryable_client_error(_make_api_error(400)) is True
    assert _is_non_retryable_client_error(_make_api_error(401)) is True
    assert _is_non_retryable_client_error(_make_api_error(403)) is True
    assert _is_non_retryable_client_error(_make_api_error(404)) is True
    assert _is_non_retryable_client_error(_make_api_error(429)) is False
    assert _is_non_retryable_client_error(_make_api_error(503)) is False


def test_is_retryable_excludes_quota_and_4xx() -> None:
    assert _is_retryable(_make_api_error(429, "RESOURCE_EXHAUSTED")) is False
    assert _is_retryable(_make_api_error(400)) is False
    assert _is_retryable(_make_api_error(404)) is False
    assert _is_retryable(_make_api_error(503)) is True


def test_extract_retry_after_from_retry_info() -> None:
    details = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "27s"}]
    assert _extract_retry_after_seconds(details) == 27


def test_extract_retry_after_from_metadata() -> None:
    details = [{"metadata": {"retryDelay": "12s"}}]
    assert _extract_retry_after_seconds(details) == 12


def test_extract_retry_after_missing() -> None:
    assert _extract_retry_after_seconds(None) is None
    assert _extract_retry_after_seconds([]) is None
    assert _extract_retry_after_seconds([{"unrelated": "value"}]) is None


# ---------------------------------------------------------------------------
# Embeddings (the only remaining GeminiProvider call path -- generation
# moved to OpenRouterProvider, see test_llm_openrouter.py)
# ---------------------------------------------------------------------------


def _embed_response(values):
    embedding = MagicMock(values=values)
    return MagicMock(embeddings=[embedding] if values is not None else [])


def test_embed_text_success(mock_provider: GeminiProvider) -> None:
    mock_provider._client.models.embed_content.return_value = _embed_response([0.1] * 1536)

    values = mock_provider.embed_text("hi")

    assert len(values) == 1536


def test_embed_text_404_does_not_retry_and_raises_llmerror(mock_provider: GeminiProvider) -> None:
    """A 404 should raise LLMError and not silently retry on a missing model."""
    mock_provider._client.models.embed_content.side_effect = _make_api_error(404, "NOT_FOUND", "model missing")

    with pytest.raises(LLMError):
        mock_provider.embed_text("hi")

    assert mock_provider._client.models.embed_content.call_count == 1


def test_embed_text_429_raises_quota_error_without_retry(mock_provider: GeminiProvider) -> None:
    """A 429 should be mapped to LLMQuotaError and must NOT trigger retries."""
    mock_provider._client.models.embed_content.side_effect = _make_api_error(
        429,
        "RESOURCE_EXHAUSTED",
        "Quota exceeded",
        details=[{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "27s"}],
    )

    with pytest.raises(LLMQuotaError) as exc_info:
        mock_provider.embed_text("hi")

    err = exc_info.value
    assert err.status_code == 429
    assert err.retry_after == 27
    assert err.provider == "gemini"
    assert mock_provider._client.models.embed_content.call_count == 1


def test_embed_text_5xx_retries_once(mock_provider: GeminiProvider) -> None:
    """A 503 should be retried once and then surface the LLMError."""
    mock_provider._client.models.embed_content.side_effect = [
        _make_api_error(503, "UNAVAILABLE", "transient"),
        _make_api_error(503, "UNAVAILABLE", "still down"),
    ]

    with pytest.raises(LLMError):
        mock_provider.embed_text("hi")

    # tenacity: stop_after_attempt(2) means at most 2 attempts.
    assert mock_provider._client.models.embed_content.call_count == 2


def test_embed_text_5xx_then_success_succeeds(mock_provider: GeminiProvider) -> None:
    """First call transient 5xx, second call OK."""
    mock_provider._client.models.embed_content.side_effect = [
        _make_api_error(503, "UNAVAILABLE", "transient"),
        _embed_response([0.2] * 1536),
    ]

    values = mock_provider.embed_text("hi")
    assert len(values) == 1536
    assert mock_provider._client.models.embed_content.call_count == 2
