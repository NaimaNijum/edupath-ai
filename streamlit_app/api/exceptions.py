from __future__ import annotations


class BackendError(Exception):
    """A user-safe error raised for any failed backend call.

    ``message`` is always safe to show directly in the UI -- no raw
    tracebacks or provider error bodies are ever surfaced to the caller.
    """

    def __init__(self, message: str, *, status_code: int | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after

    @property
    def is_quota_error(self) -> bool:
        return self.status_code == 429

    @property
    def is_connection_error(self) -> bool:
        return self.status_code is None
