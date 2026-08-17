from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.workflow import (
    AgentExecutionRead,
    AgentMessageRead,
    ApprovalDecisionRequest,
    WorkflowCreateRequest,
    WorkflowExecutionResponse,
    WorkflowLogsResponse,
    WorkflowRead,
)
from app.services.export import build_workflow_workbook
from app.services.workflow import WorkflowNotResumableError, WorkflowService

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


@router.get("", response_model=list[WorkflowRead])
async def list_workflows(
    profile_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRead]:
    return await service.list_for_profile(session, profile_id)


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


@router.post("/{workflow_id}/approve", response_model=WorkflowExecutionResponse)
async def approve_workflow(
    workflow_id: UUID,
    request: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """Resumes a workflow genuinely paused at the approval_gate interrupt,
    continuing on to sop_agent (if planned)."""
    try:
        return await service.resume(session, workflow_id, decision="approve", opportunity_id=request.opportunity_id)
    except WorkflowNotResumableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{workflow_id}/reject", response_model=WorkflowExecutionResponse)
async def reject_workflow(
    workflow_id: UUID,
    request: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionResponse:
    """Resumes a workflow genuinely paused at the approval_gate interrupt,
    ending it without SOP generation."""
    try:
        return await service.resume(session, workflow_id, decision="reject", opportunity_id=request.opportunity_id)
    except WorkflowNotResumableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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


@router.get("/{workflow_id}/export.xlsx")
async def export_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: WorkflowService = Depends(get_workflow_service),
) -> StreamingResponse:
    result = await service.get_workflow_result(session, workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workbook_bytes = build_workflow_workbook(
        candidate_opportunities=result.get("candidate_opportunities") or [],
        eligibility_verdicts=result.get("eligibility_verdicts") or [],
        research_match_verdicts=result.get("research_match_verdicts") or [],
        ranked_opportunities=result.get("ranked_opportunities") or [],
    )
    return StreamingResponse(
        iter([workbook_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=edupath-workflow-{workflow_id}.xlsx"},
    )

