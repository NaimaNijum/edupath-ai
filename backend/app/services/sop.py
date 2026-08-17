from __future__ import annotations

from app.core.config import settings
from app.llm.gemini import get_gemini_provider
from app.repositories.sop import SOPRepository
from app.schemas.sop import SOPGenerateRequest, SOPResponse, SOPReviseRequest


class SOPService:
    def __init__(self, repository: SOPRepository | None = None, provider=None) -> None:
        self._repository = repository or SOPRepository()
        self._provider = provider or get_gemini_provider()

    async def generate(self, request: SOPGenerateRequest) -> SOPResponse:
        prompt = request.prompt or (
            f"Draft an SOP for profile {request.profile_id} targeting {request.target_program or 'the target program'}"
            f" at {request.target_university or 'the target university'}."
        )
        result = self._provider.generate(
            prompt,
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
        )
        return SOPResponse(title="Generated SOP Draft", content=result.text, status="draft")

    async def revise(self, request: SOPReviseRequest) -> SOPResponse:
        prompt = f"Revise SOP {request.sop_id} for profile {request.profile_id} using this feedback: {request.feedback}"
        result = self._provider.generate(
            prompt,
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
        )
        return SOPResponse(sop_id=request.sop_id, title="Revised SOP Draft", content=result.text, status="draft")
