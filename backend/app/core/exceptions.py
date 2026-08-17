class EduPathError(Exception):
    """Base domain error for EduPath AI."""


class ConfigurationError(EduPathError):
    """Raised when required configuration is missing or invalid."""


class LLMError(EduPathError):
    """Raised when the Gemini provider cannot complete a request."""


class LLMQuotaError(LLMError):
    """Raised when the upstream LLM provider rejects the request because the
    account / model quota is exhausted.

    The original provider error is preserved on ``__cause__`` so callers can
    inspect it. Instances also expose the structured retry information returned
    by the provider so the HTTP layer can surface it to the client.
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        model: str | None = None,
        status_code: int | None = None,
        retry_after: float | None = None,
        quota_message: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.retry_after = retry_after
        self.quota_message = quota_message or message

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"LLMQuotaError(provider={self.provider!r}, model={self.model!r}, "
            f"status_code={self.status_code!r}, retry_after={self.retry_after!r})"
        )


class ToolError(EduPathError):
    """Raised when a tool invocation fails."""


class WorkflowError(EduPathError):
    """Raised when the LangGraph workflow cannot proceed."""
