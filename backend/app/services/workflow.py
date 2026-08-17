from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EduPathError, WorkflowError
from app.graph.workflow import build_graph
from app.repositories.workflow import WorkflowRepository
from app.schemas.workflow import (
    AgentExecutionRead,
    AgentMessageRead,
    WorkflowCreateRequest,
    WorkflowExecutionResponse,
    WorkflowRead,
)
from app.services.memory import MemoryService
from app.services.tooling import ToolingService


class WorkflowService:
    def __init__(
        self,
        provider=None,
        repository: WorkflowRepository | None = None,
        graph=None,
        memory_service: MemoryService | None = None,
        tooling_service: ToolingService | None = None,
    ) -> None:
        self._graph = graph or build_graph(provider=provider)
        self._repository = repository or WorkflowRepository()
        self._memory_service = memory_service or MemoryService()
        self._tooling_service = tooling_service or ToolingService()

    async def execute(self, session: AsyncSession, request: WorkflowCreateRequest) -> WorkflowExecutionResponse:
        profile_id = UUID(request.student_profile_id) if request.student_profile_id else None
        started_at = datetime.now(UTC)
        workflow = await self._repository.create_workflow_execution(
            session,
            profile_id=profile_id,
            workflow_type=request.workflow_type,
            user_request=request.user_request,
            started_at=started_at,
        )

        memory_references = await self._memory_service.load_context(
            session,
            profile_id,
            request.user_request,
            limit=5,
        )

        tool_results = await self._tooling_service.build_context(session, request.user_request)

        state = {
            "workflow_id": str(workflow.id),
            "workflow_type": request.workflow_type,
            "user_request": request.user_request,
            "user_input": request.user_request,
            "student_profile_id": request.student_profile_id,
            "workflow_status": "running",
            "approval_status": "not_required",
            "execution_plan": [],
            "plan_index": 0,
            "agent_results": [],
            "agent_messages": [],
            "memory_references": memory_references,
            "tool_results": tool_results,
            "errors": [],
        }

        try:
            try:
                result = await asyncio.to_thread(
                    self._graph.invoke, state, {"configurable": {"thread_id": str(workflow.id)}}
                )
            except TypeError as exc:
                # Lightweight test/deterministic graph adapters may not expose
                # LangGraph's optional config parameter.
                if "positional arguments" not in str(exc):
                    raise
                result = await asyncio.to_thread(self._graph.invoke, state)
        except EduPathError as exc:
            # Preserve domain errors (LLMQuotaError, LLMError, ToolError, ...)
            # so the FastAPI exception handler can map them to the correct
            # HTTP status (e.g. 429 for quota exhaustion) instead of the
            # generic 500 WorkflowError.
            await self._repository.fail_workflow_execution(session, workflow.id, str(exc), completed_at=datetime.now(UTC))
            raise
        except Exception as exc:
            await self._repository.fail_workflow_execution(session, workflow.id, str(exc), completed_at=datetime.now(UTC))
            raise WorkflowError(str(exc)) from exc

        completed_at = datetime.now(UTC)
        response = WorkflowExecutionResponse.model_validate({
            **result,
            "workflow_id": str(workflow.id),
            "workflow_type": request.workflow_type,
            "started_at": started_at,
            "completed_at": completed_at,
            "token_usage": self._repository.summarize_token_usage(result.get("agent_results", [])),
            "estimated_cost_usd": self._repository.summarize_cost(result.get("agent_results", [])),
        })

        await self._repository.save_workflow_result(session, workflow.id, response, raw_state=result, completed_at=completed_at)
        if hasattr(self._memory_service, "record_workflow_context"):
            await self._memory_service.record_workflow_context(
                session, profile_id, user_request=request.user_request, workflow_id=str(workflow.id), profile=result.get("profile")
            )
        return response

    async def get_workflow(self, session: AsyncSession, workflow_id: UUID) -> WorkflowRead | None:
        workflow = await self._repository.get_workflow_execution(session, workflow_id)
        return WorkflowRead.model_validate(workflow) if workflow else None

    async def list_agents(self, session: AsyncSession, workflow_id: UUID) -> list[AgentExecutionRead]:
        items = await self._repository.list_agent_executions(session, workflow_id)
        return [AgentExecutionRead.model_validate(item) for item in items]

    async def list_messages(self, session: AsyncSession, workflow_id: UUID) -> list[AgentMessageRead]:
        items = await self._repository.list_agent_messages(session, workflow_id)
        return [AgentMessageRead.model_validate(item) for item in items]

    async def list_logs(self, session: AsyncSession, workflow_id: UUID) -> list[dict[str, Any]]:
        return await self._repository.list_workflow_logs(session, workflow_id)

    async def transition_workflow(self, session: AsyncSession, workflow_id: UUID, status: str) -> WorkflowRead | None:
        workflow = await self._repository.update_workflow_status(session, workflow_id, status)
        return WorkflowRead.model_validate(workflow) if workflow else None
