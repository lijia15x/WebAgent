from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    original_question: str
    selected_skill: str
    task: str
    confidence: float
    loaded_instructions: str
    plan: dict[str, Any]
    command_results: list[dict[str, Any]]
    completed_work: list[str]
    attempted_skills: list[str]
    remaining_goal: str
    command_rounds: int
    skill_switches: int
    error: str
    final_answer: str
    answer_streamed: bool