from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ShortTermMemory:
    workflow_id: str
    agent_messages: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def snapshot(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "agent_messages": list(self.agent_messages),
            "tool_results": list(self.tool_results),
            "errors": list(self.errors),
        }
