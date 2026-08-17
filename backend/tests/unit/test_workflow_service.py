from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.schemas.agent import AgentMessage, AgentResult
from app.schemas.workflow import WorkflowCreateRequest
from app.services.workflow import WorkflowService


@dataclass
class FakeWorkflowRecord:
    id: UUID
    user_request: str
    workflow_type: str


class FakeGraph:
    def __init__(self) -> None:
        self.last_state: dict | None = None

    def invoke(self, state: dict) -> dict:
        self.last_state = state
        return {
            "workflow_status": "completed",
            "execution_plan": ["profile_agent", "verification_agent"],
            "plan_index": 2,
            "next_agent": "__end__",
            "agent_results": [
                AgentResult(
                    agent_name="profile_agent",
                    summary="Profile matched.",
                    supervisor_message="Profile ready.",
                    token_usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
                    estimated_cost_usd=0.00001,
                ),
                AgentResult(
                    agent_name="verification_agent",
                    summary="Verified.",
                    supervisor_message="Verified.",
                    token_usage={"input_tokens": 12, "output_tokens": 18, "total_tokens": 30},
                    estimated_cost_usd=0.00002,
                ),
            ],
            "agent_messages": [
                AgentMessage(sender="supervisor", receiver="profile_agent", message_type="handoff", content="start"),
                AgentMessage(sender="verification_agent", receiver="supervisor", message_type="analysis", content="ok"),
            ],
            "final_response": "Done",
            "errors": [],
        }


class FakeRepository:
    def __init__(self) -> None:
        self.created: FakeWorkflowRecord | None = None
        self.saved_response = None
        self.saved_raw_state = None
        self.failed_error: str | None = None

    async def create_workflow_execution(self, session, *, profile_id, workflow_type, user_request, started_at):
        self.created = FakeWorkflowRecord(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            user_request=user_request,
            workflow_type=workflow_type,
        )
        return self.created

    async def save_workflow_result(self, session, workflow_id, response, *, raw_state, completed_at):
        self.saved_response = response
        self.saved_raw_state = raw_state
        self.saved_workflow_id = workflow_id

    async def fail_workflow_execution(self, session, workflow_id, error, *, completed_at):
        self.failed_error = error

    def summarize_token_usage(self, agent_results):
        total_input = sum(int(result.token_usage.get("input_tokens", 0)) for result in agent_results)
        total_output = sum(int(result.token_usage.get("output_tokens", 0)) for result in agent_results)
        total_tokens = sum(int(result.token_usage.get("total_tokens", 0)) for result in agent_results)
        cost = sum(float(result.estimated_cost_usd) for result in agent_results)
        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost,
        }

    def summarize_cost(self, agent_results):
        return float(self.summarize_token_usage(agent_results)["estimated_cost_usd"])


class FakeMemoryService:
    async def load_context(self, session, profile_id, query_text, limit=5):
        return [
            {
                "id": "memory-1",
                "profile_id": str(profile_id) if profile_id else None,
                "memory_type": "profile",
                "scope": "long_term",
                "content": {"note": "prefers funded PhD programs"},
                "source": "test",
            }
        ]


class FakeToolingService:
    async def build_context(self, session, query):
        return [
            {
                "tool_name": "university_search",
                "query": query,
                "results": [{"title": "Test University"}],
            }
        ]


@pytest.mark.asyncio
async def test_workflow_service_persists_execution_and_records() -> None:
    graph = FakeGraph()
    repository = FakeRepository()
    service = WorkflowService(repository=repository, graph=graph, memory_service=FakeMemoryService(), tooling_service=FakeToolingService())
    session = SimpleNamespace()

    response = await service.execute(
        session,
        WorkflowCreateRequest(
            user_request="I am a CSE student with GPA 3.7 and want a funded PhD in AI in USA.",
            student_profile_id=None,
            workflow_type="opportunity_discovery",
        ),
    )

    assert repository.created is not None
    assert repository.saved_workflow_id == repository.created.id
    assert response.workflow_status == "completed"
    assert response.workflow_id == "11111111-1111-1111-1111-111111111111"
    assert response.token_usage["total_tokens"] == 60
    assert len(response.agent_results) == 2
    assert graph.last_state is not None
    assert graph.last_state["workflow_id"] == "11111111-1111-1111-1111-111111111111"
    assert graph.last_state["workflow_type"] == "opportunity_discovery"
    assert graph.last_state["memory_references"]
    assert graph.last_state["tool_results"]


