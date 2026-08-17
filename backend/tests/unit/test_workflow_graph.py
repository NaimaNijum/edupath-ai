from __future__ import annotations

from collections.abc import Callable

from app.graph.workflow import build_graph
from app.graph.routing import build_execution_plan
from app.schemas.agent import AgentMessage, SupervisorDecision, TokenUsage


class FakeResult:
    def __init__(self, text: str, input_tokens: int = 12, output_tokens: int = 24) -> None:
        self.text = text
        self.usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=0.0,
        )


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate_structured(self, prompt: str, *, response_model, model=None, temperature=None, system_instruction=None, context=None):
        self.calls.append(response_model.__name__)
        name = response_model.__name__

        if name == "SupervisorDecision":
            # The supervisor prompt embeds the user request; we don't parse it,
            # but build_execution_plan is deterministic and tested elsewhere.
            plan = [
                "profile_agent",
                "professor_agent",
                "university_agent",
                "scholarship_agent",
                "eligibility_agent",
                "sop_agent",
                "verification_agent",
            ]
            return SupervisorDecision(
                next_agent=plan[0],
                reason="Initial planning.",
                execution_plan=plan,
            ), FakeResult(text="supervisor")

        if name == "ProfileAgentOutput":
            payload = {
                "summary": "Student profile indicates CSE, ML focus, and PhD intent.",
                "key_findings": ["CSE background", "AI/ML interest", "fully funded PhD target"],
                "recommended_next_agent": "professor_agent",
                "supervisor_message": "Profile signals are ready for professor matching.",
                "next_agent_message": "Look for AI/ML supervisors.",
                "confidence": 0.91,
            }
        elif name == "ProfessorAgentOutput":
            payload = {
                "summary": "Potential professors should align with AI and ML research.",
                "key_findings": ["Research fit needed", "Prefer USA institutions"],
                "recommended_next_agent": "university_agent",
                "supervisor_message": "Professor shortlist should feed university selection.",
                "next_agent_message": "Map professors to universities.",
                "confidence": 0.86,
            }
        elif name == "UniversityAgentOutput":
            payload = {
                "summary": "Universities with strong AI/ML programs are prioritized.",
                "key_findings": ["Program fit", "Country fit"],
                "recommended_next_agent": "scholarship_agent",
                "supervisor_message": "University selection is ready for funding search.",
                "next_agent_message": "Find funding for these universities.",
                "confidence": 0.84,
            }
        elif name == "ScholarshipAgentOutput":
            payload = {
                "summary": "Funding pathways include fully funded doctoral scholarships.",
                "key_findings": ["Funding required", "Need deadline review"],
                "recommended_next_agent": "eligibility_agent",
                "supervisor_message": "Funding options need eligibility review.",
                "next_agent_message": "Check scholarship criteria.",
                "confidence": 0.88,
            }
        elif name == "EligibilityAgentOutput":
            payload = {
                "summary": "Eligibility appears plausible for funded PhD opportunities.",
                "key_findings": ["GPA looks competitive", "Check publication requirements"],
                "recommended_next_agent": "sop_agent",
                "supervisor_message": "Eligibility checks are ready for SOP support.",
                "next_agent_message": "Improve SOP for applications.",
                "confidence": 0.8,
            }
        elif name == "SOPAgentOutput":
            payload = {
                "summary": "SOP should emphasize AI research and funding fit.",
                "key_findings": ["Need research narrative", "Need motivation clarity"],
                "recommended_next_agent": "verification_agent",
                "supervisor_message": "SOP guidance is ready for verification.",
                "next_agent_message": "Verify overall recommendations.",
                "confidence": 0.83,
            }
        elif name == "VerificationAgentOutput":
            payload = {
                "summary": "Cross-agent reasoning is internally consistent.",
                "key_findings": ["Profile aligns with professor search", "Funding and eligibility are consistent"],
                "recommended_next_agent": "__end__",
                "supervisor_message": "The workflow is verified and ready to close.",
                "next_agent_message": None,
                "confidence": 0.95,
            }
        else:
            raise AssertionError(f"Unexpected response model: {name}")

        return response_model.model_validate(payload), FakeResult(text=response_model.model_validate(payload).model_dump_json())


def test_workflow_runs_through_all_agents():
    graph = build_graph(provider=FakeProvider())

    result = graph.invoke(
        {
            "user_request": "I am a CSE student with GPA 3.7 and want a funded PhD in AI in USA.",
            "user_input": "I am a CSE student with GPA 3.7 and want a funded PhD in AI in USA.",
            "workflow_status": "running",
            "approval_status": "not_required",
            "execution_plan": [],
            "plan_index": 0,
            "agent_results": [],
            "agent_messages": [],
            "memory_references": [],
            "tool_results": [],
            "errors": [],
        }
    )

    assert result["workflow_status"] == "completed"
    assert result["next_agent"] == "__end__"
    assert len(result["agent_results"]) == 7
    assert [item.agent_name for item in result["agent_results"]] == [
        "profile_agent",
        "professor_agent",
        "university_agent",
        "scholarship_agent",
        "eligibility_agent",
        "sop_agent",
        "verification_agent",
    ]
    assert any(message.sender == "verification_agent" for message in result["agent_messages"])


from app.agents.profile.agent import build_profile_agent, ProfileAgentOutput

def test_profile_agent_unit():
    """Tests the profile agent in isolation."""
    # Arrange
    provider = FakeProvider()
    profile_agent = build_profile_agent(provider=provider)
    initial_state = {
        "user_request": "I want a funded PhD in AI.",
        "agent_results": [],
        "agent_messages": [],
    }

    # Act
    result_state = profile_agent(initial_state)

    # Assert
    assert "profile" in result_state
    assert len(result_state["agent_results"]) == 1
    
    agent_result = result_state["agent_results"][0]
    assert agent_result.agent_name == "profile_agent"
    assert agent_result.summary == "Student profile indicates CSE, ML focus, and PhD intent."
    
    profile_output = ProfileAgentOutput.model_validate(result_state["profile"])
    assert profile_output.summary == "Student profile indicates CSE, ML focus, and PhD intent."
    assert profile_output.recommended_next_agent == "professor_agent"
    
    assert len(result_state["agent_messages"]) == 1
    agent_message = result_state["agent_messages"][0]
    assert agent_message.sender == "profile_agent"
    assert agent_message.receiver == "supervisor"
