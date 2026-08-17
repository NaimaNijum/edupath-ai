from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.workflow import (
    AgentExecutionRead,
    AgentMessageRead,
    WorkflowCreateRequest,
    WorkflowExecutionResponse,
    WorkflowLogsResponse,
    WorkflowRead,
)
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_service() -> WorkflowService:
    return WorkflowService()


@router.post("", response_model=WorkflowExecutionResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    return await service.execute(session, request)


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    workflow = await service.get_workflow(session, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/{workflow_id}/pause", response_model=WorkflowRead)
async def pause_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    workflow = await service.transition_workflow(session, workflow_id, "paused")
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/{workflow_id}/resume", response_model=WorkflowRead)
async def resume_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    workflow = await service.transition_workflow(session, workflow_id, "running")
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/{workflow_id}/approve", response_model=WorkflowRead)
async def approve_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    workflow = await service.transition_workflow(session, workflow_id, "approved")
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/{workflow_id}/reject", response_model=WorkflowRead)
async def reject_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    workflow = await service.transition_workflow(session, workflow_id, "rejected")
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/{workflow_id}/retry", response_model=WorkflowRead)
async def retry_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    workflow = await service.transition_workflow(session, workflow_id, "retrying")
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/{workflow_id}/agents", response_model=list[AgentExecutionRead])
async def get_workflow_agents(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> list[AgentExecutionRead]:
    return await service.list_agents(session, workflow_id)


@router.get("/{workflow_id}/messages", response_model=list[AgentMessageRead])
async def get_workflow_messages(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> list[AgentMessageRead]:
    return await service.list_messages(session, workflow_id)


@router.get("/{workflow_id}/logs", response_model=WorkflowLogsResponse)
async def get_workflow_logs(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowLogsResponse:
    return WorkflowLogsResponse(events=await service.list_logs(session, workflow_id))

