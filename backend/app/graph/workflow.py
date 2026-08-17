from langgraph.graph import END, START, StateGraph

from app.agents.eligibility.agent import build_eligibility_agent
from app.agents.professor.agent import build_professor_agent
from app.agents.profile.agent import build_profile_agent
from app.agents.scholarship.agent import build_scholarship_agent
from app.agents.sop.agent import build_sop_agent
from app.agents.supervisor.agent import build_supervisor_agent
from app.graph.checkpoints import build_checkpointer
from app.agents.university.agent import build_university_agent
from app.agents.verification.agent import build_verification_agent
from app.graph.state import EduPathState


def build_graph(provider=None):
    graph = StateGraph(EduPathState)

    graph.add_node("supervisor", build_supervisor_agent(provider))
    graph.add_node("profile_agent", build_profile_agent(provider))
    graph.add_node("professor_agent", build_professor_agent(provider))
    graph.add_node("university_agent", build_university_agent(provider))
    graph.add_node("scholarship_agent", build_scholarship_agent(provider))
    graph.add_node("eligibility_agent", build_eligibility_agent(provider))
    graph.add_node("sop_agent", build_sop_agent(provider))
    graph.add_node("verification_agent", build_verification_agent(provider))

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_agent", "__end__"),
        {
            "profile_agent": "profile_agent",
            "professor_agent": "professor_agent",
            "university_agent": "university_agent",
            "scholarship_agent": "scholarship_agent",
            "eligibility_agent": "eligibility_agent",
            "sop_agent": "sop_agent",
            "verification_agent": "verification_agent",
            "__end__": END,
        },
    )

    graph.add_edge("profile_agent", "supervisor")
    graph.add_edge("professor_agent", "supervisor")
    graph.add_edge("university_agent", "supervisor")
    graph.add_edge("scholarship_agent", "supervisor")
    graph.add_edge("eligibility_agent", "supervisor")
    graph.add_edge("sop_agent", "supervisor")
    graph.add_edge("verification_agent", "supervisor")

    # Production graphs use the durable-in-process checkpointer. Test graphs
    # deliberately use injected providers and remain easy to invoke directly.
    return graph.compile(checkpointer=build_checkpointer() if provider is None else None)
