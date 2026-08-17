"""Tests for Gemini error classification, retry policy, and structured output."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.core.exceptions import LLMError, LLMQuotaError
from app.llm.gemini import (
    GeminiProvider,
    _extract_retry_after_seconds,
    _is_non_retryable_client_error,
    _is_quota_error,
    _is_retryable,
    _is_transient_5xx,
)


class SampleModel(BaseModel):
    name: str
    value: int


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
# Generation
# ---------------------------------------------------------------------------


def test_generate_success_returns_text(mock_provider: GeminiProvider) -> None:
    mock_provider._client.models.generate_content.return_value = MagicMock(
        text="hello",
        usage_metadata=MagicMock(prompt_token_count=5, candidates_token_count=7, total_token_count=12),
    )

    result = mock_provider.generate("hi")

    assert result.text == "hello"
    assert result.usage.total_tokens == 12


def test_generate_404_does_not_retry_and_raises_llmerror(mock_provider: GeminiProvider) -> None:
    """A 404 should raise LLMError and not silently retry on a missing model."""
    mock_provider._client.models.generate_content.side_effect = _make_api_error(404, "NOT_FOUND", "model missing")

    with pytest.raises(LLMError):
        mock_provider.generate("hi")

    assert mock_provider._client.models.generate_content.call_count == 1


def test_generate_429_raises_quota_error_without_retry(mock_provider: GeminiProvider) -> None:
    """A 429 should be mapped to LLMQuotaError and must NOT trigger retries."""
    mock_provider._client.models.generate_content.side_effect = _make_api_error(
        429,
        "RESOURCE_EXHAUSTED",
        "Quota exceeded",
        details=[{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "27s"}],
    )

    with pytest.raises(LLMQuotaError) as exc_info:
        mock_provider.generate("hi")

    err = exc_info.value
    assert err.status_code == 429
    assert err.retry_after == 27
    assert err.provider == "gemini"
    assert err.model == mock_provider._client.models.generate_content.call_args.kwargs["model"]
    assert mock_provider._client.models.generate_content.call_count == 1


def test_generate_5xx_retries_once(mock_provider: GeminiProvider) -> None:
    """A 503 should be retried once and then surface the LLMError."""
    mock_provider._client.models.generate_content.side_effect = [
        _make_api_error(503, "UNAVAILABLE", "transient"),
        _make_api_error(503, "UNAVAILABLE", "still down"),
    ]

    with pytest.raises(LLMError):
        mock_provider.generate("hi")

    # tenacity: stop_after_attempt(2) means at most 2 attempts.
    assert mock_provider._client.models.generate_content.call_count == 2


def test_generate_5xx_then_success_succeeds(mock_provider: GeminiProvider) -> None:
    """First call transient 5xx, second call OK."""
    ok_response = MagicMock(
        text="ok",
        usage_metadata=MagicMock(prompt_token_count=1, candidates_token_count=1, total_token_count=2),
    )
    mock_provider._client.models.generate_content.side_effect = [
        _make_api_error(503, "UNAVAILABLE", "transient"),
        ok_response,
    ]

    result = mock_provider.generate("hi")
    assert result.text == "ok"
    assert mock_provider._client.models.generate_content.call_count == 2


# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------


def test_generate_structured_passes_response_schema(mock_provider: GeminiProvider) -> None:
    """Structured output must set response_schema so Gemini enforces the model."""
    mock_provider._client.models.generate_content.return_value = MagicMock(
        text=json.dumps({"name": "n", "value": 1}),
        usage_metadata=MagicMock(prompt_token_count=1, candidates_token_count=1, total_token_count=2),
    )

    parsed, _ = mock_provider.generate_structured("p", response_model=SampleModel)
    assert parsed.name == "n"
    assert parsed.value == 1

    config = mock_provider._client.models.generate_content.call_args.kwargs["config"]
    assert config["response_schema"] is SampleModel
    assert config["response_mime_type"] == "application/json"


def test_generate_structured_quota_error_propagates(mock_provider: GeminiProvider) -> None:
    mock_provider._client.models.generate_content.side_effect = _make_api_error(
        429, "RESOURCE_EXHAUSTED", "Quota", details=[{"retryDelay": "5s"}]
    )
    with pytest.raises(LLMQuotaError) as exc_info:
        mock_provider.generate_structured("p", response_model=SampleModel)
    assert exc_info.value.retry_after == 5


def test_generate_structured_invalid_json_raises_llmerror(mock_provider: GeminiProvider) -> None:
    """A trailing comma in JSON should produce a clear LLMError."""
    mock_provider._client.models.generate_content.return_value = MagicMock(
        text='{"name": "n", "value": 1,}',
        usage_metadata=MagicMock(prompt_token_count=1, candidates_token_count=1, total_token_count=2),
    )

    with pytest.raises(LLMError, match="Invalid JSON response from Gemini"):
        mock_provider.generate_structured("p", response_model=SampleModel)


def test_generate_structured_schema_violation_raises_llmerror(mock_provider: GeminiProvider) -> None:
    """A schema-violating response (array when int expected) raises LLMError."""
    mock_provider._client.models.generate_content.return_value = MagicMock(
        text='{"name": "n", "value": [1, 2]}',
        usage_metadata=MagicMock(prompt_token_count=1, candidates_token_count=1, total_token_count=2),
    )

    with pytest.raises(LLMError, match="Gemini response failed Pydantic validation"):
        mock_provider.generate_structured("p", response_model=SampleModel)
