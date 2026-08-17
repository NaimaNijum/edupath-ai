from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, TypeVar

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import BaseModel, ValidationError
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
from app.llm.usage import TokenUsage, estimate_cost_usd

T = TypeVar("T", bound=BaseModel)

_logger = get_logger(component="llm")


@dataclass(slots=True)
class LLMResult:
    text: str
    usage: TokenUsage


@dataclass(slots=True)
class LLMCallContext:
    """Request-level metadata attached to a Gemini call purely for
    observability. Never sent to the Gemini API and must never carry API
    keys or raw user content.
    """

    workflow_id: str | None = None
    agent_name: str | None = None
    purpose: str | None = None
    call_number: int | None = None

    def fields(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "purpose": self.purpose,
            "call_number": self.call_number,
        }


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
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        system_instruction: str | None = None,
        context: LLMCallContext | None = None,
    ) -> LLMResult:
        model_name = model or settings.gemini_model
        ctx = context or LLMCallContext(purpose="generate")
        attempt_counter: dict[str, int] = {}

        try:
            response = self._generate_content(
                model_name,
                prompt,
                temperature=temperature,
                system_instruction=system_instruction,
                json_mode=False,
                context=ctx,
                attempt_counter=attempt_counter,
            )
        except LLMError:
            raise
        except genai_errors.APIError as exc:
            if _is_quota_error(exc):
                _logger.warning("gemini_call_quota_exhausted", model=model_name, **ctx.fields())
                raise _build_quota_error(exc, provider="gemini", model=model_name) from exc
            _logger.warning("gemini_call_failed", model=model_name, error_type=exc.__class__.__name__, **ctx.fields())
            raise LLMError(f"Gemini request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - exercised through higher-level tests
            _logger.warning("gemini_call_failed", model=model_name, error_type=exc.__class__.__name__, **ctx.fields())
            raise LLMError(f"Gemini request failed: {exc}") from exc

        usage = self._extract_usage(response, model_name)
        text = getattr(response, "text", "") or ""
        _logger.info("gemini_call_success", model=model_name, total_tokens=usage.total_tokens, **ctx.fields())
        return LLMResult(text=text, usage=usage)

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential_jitter(initial=0.5, max=8, jitter=1),
        stop=stop_after_attempt(2),
        reraise=True,
        before_sleep=_log_retry_attempt,
    )
    def _generate_content(
        self,
        model_name: str,
        prompt: str,
        *,
        temperature: float | None,
        system_instruction: str | None,
        json_mode: bool = False,
        response_schema: type[BaseModel] | dict | None = None,
        context: LLMCallContext | None = None,
        attempt_counter: dict[str, int] | None = None,
    ):
        if attempt_counter is not None:
            attempt_counter["count"] = attempt_counter.get("count", 0) + 1
        attempt = attempt_counter.get("count", 1) if attempt_counter is not None else 1
        fields = context.fields() if isinstance(context, LLMCallContext) else {}
        _logger.info("gemini_generate_content_attempt", model=model_name, attempt=attempt, **fields)

        config: dict[str, Any] = {
            "temperature": temperature if temperature is not None else settings.gemini_temperature,
            "http_options": {"timeout": int(settings.gemini_request_timeout_seconds * 1000)},
            # Agents do not use function-calling tools. Disable AFC explicitly
            # to silence the SDK's "Direct use of automatic function calling
            # (AFC) in Models.generate_content is not recommended" warning.
            "automatic_function_calling": genai_types.AutomaticFunctionCallingConfig(disable=True),
        }
        if system_instruction:
            config["system_instruction"] = system_instruction
        if json_mode:
            config["response_mime_type"] = "application/json"
        if response_schema is not None:
            # Schema-enforced structured output. The Gemini SDK accepts a
            # Pydantic model class directly and constrains the response to it.
            config["response_schema"] = response_schema
            config["response_mime_type"] = "application/json"

        return self.client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )

    def generate_structured(
        self,
        prompt: str,
        *,
        response_model: type[T],
        model: str | None = None,
        temperature: float | None = None,
        system_instruction: str | None = None,
        context: LLMCallContext | None = None,
    ) -> tuple[T, LLMResult]:
        model_name = model or settings.gemini_model
        sys_instruction = system_instruction or "Output must be valid JSON."
        ctx = context or LLMCallContext()
        if not ctx.purpose:
            ctx.purpose = response_model.__name__
        attempt_counter: dict[str, int] = {}

        try:
            response = self._generate_content(
                model_name,
                prompt,
                temperature=temperature,
                system_instruction=sys_instruction,
                json_mode=True,
                response_schema=response_model,
                context=ctx,
                attempt_counter=attempt_counter,
            )
        except LLMError:
            raise
        except genai_errors.APIError as exc:
            if _is_quota_error(exc):
                _logger.warning("gemini_call_quota_exhausted", model=model_name, **ctx.fields())
                raise _build_quota_error(exc, provider="gemini", model=model_name) from exc
            _logger.warning("gemini_call_failed", model=model_name, error_type=exc.__class__.__name__, **ctx.fields())
            raise LLMError(
                f"Gemini structured request failed for {response_model.__name__}: {exc}"
            ) from exc
        except Exception as exc:  # pragma: no cover - exercised through higher-level tests
            _logger.warning("gemini_call_failed", model=model_name, error_type=exc.__class__.__name__, **ctx.fields())
            raise LLMError(
                f"Gemini structured request failed for {response_model.__name__}: {exc}"
            ) from exc

        raw_text = getattr(response, "text", "") or ""
        if not raw_text.strip():
            raise LLMError(f"Gemini returned an empty response for {response_model.__name__}.")

        usage = self._extract_usage(response, model_name)
        result = LLMResult(text=raw_text, usage=usage)
        _logger.info("gemini_call_success", model=model_name, total_tokens=usage.total_tokens, **ctx.fields())

        text_to_parse = self._strip_code_fence(raw_text)

        try:
            return response_model.model_validate_json(text_to_parse), result
        except json.JSONDecodeError as exc:
            error_msg = f"Invalid JSON response from Gemini for {response_model.__name__}. "
            error_msg += f"Response: ```{text_to_parse[:500]}...```"
            raise LLMError(error_msg) from exc
        except ValidationError as exc:
            # Pydantic raises ValidationError with type=json_invalid when the
            # text is not valid JSON (e.g. trailing comma). Surface that as
            # an "Invalid JSON" error so callers can distinguish parse
            # failures from genuine schema mismatches.
            is_json_error = any(
                (err.get("type") or "").startswith("json_") for err in exc.errors()
            )
            if is_json_error:
                error_msg = f"Invalid JSON response from Gemini for {response_model.__name__}. "
                error_msg += f"Response: ```{text_to_parse[:500]}...```"
                raise LLMError(error_msg) from exc
            error_msg = f"Gemini response failed Pydantic validation for {response_model.__name__}. "
            error_msg += f"Response: ```{text_to_parse[:500]}...```. "
            error_msg += f"Validation Error: {exc}"
            raise LLMError(error_msg) from exc

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        text_to_parse = text.strip()
        if text_to_parse.startswith("```json"):
            text_to_parse = text_to_parse.removeprefix("```json").removesuffix("```")
        elif text_to_parse.startswith("```"):
            text_to_parse = text_to_parse.removeprefix("```").removesuffix("```")
        return text_to_parse.strip()

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

    def _extract_usage(self, response: Any, model_name: str) -> TokenUsage:
        metadata = getattr(response, "usage_metadata", None)
        input_tokens = int(getattr(metadata, "prompt_token_count", 0) or getattr(metadata, "input_tokens", 0) or 0)
        output_tokens = int(getattr(metadata, "candidates_token_count", 0) or getattr(metadata, "output_tokens", 0) or 0)
        total_tokens = int(
            getattr(metadata, "total_token_count", 0)
            or getattr(metadata, "total_tokens", 0)
            or (input_tokens + output_tokens)
        )
        estimated_cost = estimate_cost_usd(model_name, input_tokens, output_tokens)
        available = metadata is not None
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            usage_available=available,
        )


@lru_cache
def get_gemini_provider() -> GeminiProvider:
    return GeminiProvider()
