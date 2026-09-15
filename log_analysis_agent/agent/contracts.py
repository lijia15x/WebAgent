from typing import Any, Literal

from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    skill_name: str = Field(description="Selected registered skill name or unsupported.")
    task: str = Field(description="The concrete goal assigned to the selected skill.")
    confidence: float = Field(ge=0, le=1)


class ExecutionPlan(BaseModel):
    action: Literal["run_command", "final_answer", "ask_user", "reroute_skill"]
    command: str | None = None
    answer: str | None = None
    remaining_goal: str | None = None


class CommandResult(BaseModel):
    command: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ReviewDecision(BaseModel):
    decision: Literal[
        "continue_current_skill", "reroute_skill", "complete", "ask_user"
    ]
    completed_work_summary: str = ""
    remaining_goal: str = ""
    answer: str | None = None