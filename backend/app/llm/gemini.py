from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.core.config import settings
from app.core.exceptions import LLMError, LLMQuotaError
from app.core.logging import get_logger
from app.llm.base import LLMCallContext, LLMResult

__all__ = ["LLMCallContext", "LLMResult", "GeminiProvider", "get_gemini_provider"]

_logger = get_logger(component="llm")


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------


_RETRY_DELAY_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*s", re.IGNORECASE)


def _extract_retry_after_seconds(details: Any) -> int | None:
    """Best-effort extraction of the provider's recommended retry delay.

    The Gemini REST API surfaces quota information under
    ``error.details[*].retryDelay`` in the form ``"27s"``. The
    ``google-genai`` SDK attaches the full response body to ``APIError.details``
    in addition to the structured error list, so we accept either shape. The
    value is only used as a hint for the HTTP layer; nothing here triggers an
    automatic retry on quota errors.
    """
    if not details:
        return None

    # Build the list of candidate entries: accept either the bare list of
    # error details, or a response-body-shaped dict containing an "error"
    # key with its own "details" list.
    candidates: list[Any] = []
    if isinstance(details, dict):
        error_block = details.get("error")
        if isinstance(error_block, dict):
            inner = error_block.get("details")
            if isinstance(inner, list):
                candidates.extend(item for item in inner if isinstance(item, dict))
        candidates.append(details)
    elif isinstance(details, list):
        candidates.extend(item for item in details if isinstance(item, dict))

    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        retry_delay = entry.get("retryDelay")
        if isinstance(retry_delay, str):
            match = _RETRY_DELAY_PATTERN.search(retry_delay)
            if match:
                try:
                    return int(float(match.group(1)))
                except ValueError:
                    continue
        metadata = entry.get("metadata")
        if isinstance(metadata, dict):
            value = metadata.get("retryDelay") or metadata.get("retry_delay")
            if isinstance(value, str):
                match = _RETRY_DELAY_PATTERN.search(value)
                if match:
                    try:
                        return int(float(match.group(1)))
                    except ValueError:
                        continue
    return None


def _is_quota_error(exc: BaseException) -> bool:
    """Return True when the underlying error is a 429 / RESOURCE_EXHAUSTED."""
    if isinstance(exc, genai_errors.APIError):
        if exc.code == 429:
            return True
        status = getattr(exc, "status", None)
        if isinstance(status, str) and status.upper() == "RESOURCE_EXHAUSTED":
            return True
    return False


def _is_transient_5xx(exc: BaseException) -> bool:
    """Return True for 5xx API errors that are worth retrying once."""
    if isinstance(exc, genai_errors.ServerError):
        return True
    return bool(isinstance(exc, genai_errors.APIError) and exc.code is not None and 500 <= exc.code < 600)


def _is_non_retryable_client_error(exc: BaseException) -> bool:
    """400/401/403/404 errors should not be retried."""
    if isinstance(exc, genai_errors.ClientError):
        return True
    return bool(isinstance(exc, genai_errors.APIError) and exc.code in {400, 401, 403, 404})


def _is_retryable(exc: BaseException) -> bool:
    """Tenacity predicate: only retry transient 5xx errors.

    Quota errors and non-retryable client errors are explicitly excluded so
    we do not consume additional quota on every attempt.
    """
    if _is_quota_error(exc):
        return False
    if _is_non_retryable_client_error(exc):
        return False
    return _is_transient_5xx(exc)


def _build_quota_error(exc: BaseException, *, provider: str, model: str | None) -> LLMQuotaError:
    if isinstance(exc, genai_errors.APIError):
        retry_after = _extract_retry_after_seconds(getattr(exc, "details", None))
        return LLMQuotaError(
            f"Gemini quota exhausted for model {model or 'unknown'}: {exc.message}",
            provider=provider,
            model=model,
            status_code=exc.code,
            retry_after=retry_after,
            quota_message=exc.message,
        )
    return LLMQuotaError(
        f"Gemini quota exhausted: {exc}",
        provider=provider,
        model=model,
        quota_message=str(exc),
    )


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Hook used by tenacity to log transient retries for observability.

    Quota (429) errors are excluded from the retry predicate entirely, so
    this only ever fires for transient 5xx errors, and at most once given
    ``stop_after_attempt(2)``.
    """
    ctx = retry_state.kwargs.get("context") if retry_state.kwargs else None
    fields = ctx.fields() if isinstance(ctx, LLMCallContext) else {}
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    _logger.warning(
        "gemini_transient_retry",
        attempt=retry_state.attempt_number,
        next_attempt=retry_state.attempt_number + 1,
        next_sleep=round(retry_state.next_action.sleep, 2) if retry_state.next_action else None,
        error_type=exc.__class__.__name__ if exc else None,
        **fields,
    )


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class GeminiProvider:
    """Embeddings-only provider. Text generation moved to OpenRouter -- see
    app/llm/openrouter.py -- because Gemini's free tier is too quota-limited
    for the app's generation call volume. Embeddings stayed here since
    OpenRouter has no $0 embedding model and embedding call volume is much
    lower.
    """

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def embed_text(self, text: str, *, model: str | None = None) -> list[float]:
        model_name = model or settings.embedding_model

        try:
            response = self._embed_content(model_name, text)
        except LLMError:
            raise
        except genai_errors.APIError as exc:
            if _is_quota_error(exc):
                raise _build_quota_error(exc, provider="gemini", model=model_name) from exc
            raise LLMError(f"Gemini embedding request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - integration path only
            raise LLMError(f"Gemini embedding request failed: {exc}") from exc

        embeddings = getattr(response, "embeddings", None) or []
        values = getattr(embeddings[0], "values", None) if embeddings else None
        if not values:
            raise LLMError(f"Gemini embedding response missing values for model {model_name}")
        if len(values) != settings.embedding_dimensions:
            raise LLMError(
                f"Gemini embedding dimension mismatch: expected {settings.embedding_dimensions}, got {len(values)}"
            )

        return [float(value) for value in values]

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential_jitter(initial=0.5, max=8, jitter=1),
        stop=stop_after_attempt(2),
        reraise=True,
        before_sleep=_log_retry_attempt,
    )
    def _embed_content(self, model_name: str, text: str):
        return self.client.models.embed_content(
            model=model_name,
            contents=text,
            config={
                "output_dimensionality": settings.embedding_dimensions,
                "automatic_function_calling": genai_types.AutomaticFunctionCallingConfig(disable=True),
            },
        )


@lru_cache
def get_gemini_provider() -> GeminiProvider:
    return GeminiProvider()
