import json

from langchain_core.messages import HumanMessage, SystemMessage

from ..skills.base import skill_index
from ..skills.contracts import RouteDecision


SUPERVISOR_PROMPT = """You are a task-routing supervisor.
Choose exactly one registered skill for the remaining goal and describe its task.
Return skill_name=unsupported when no skill can make progress.
Do not execute the skill, invent results, or alter the original question.

Skill index:
{skill_index}

Completed work:
{completed_work}

Previously attempted skills:
{attempted_skills}
"""


def select_skill(
    model,
    original_question: str,
    remaining_goal: str,
    completed_work: list[str],
    attempted_skills: list[str],
) -> RouteDecision:
    structured_model = model.with_structured_output(RouteDecision)
    return structured_model.invoke(
        [
            SystemMessage(
                content=SUPERVISOR_PROMPT.format(
                    skill_index=json.dumps(skill_index(), ensure_ascii=False),
                    completed_work=json.dumps(completed_work, ensure_ascii=False),
                    attempted_skills=json.dumps(attempted_skills, ensure_ascii=False),
                )
            ),
            HumanMessage(
                content=(
                    f"Original question: {original_question}\n"
                    f"Remaining goal: {remaining_goal or original_question}"
                )
            ),
        ]
    )