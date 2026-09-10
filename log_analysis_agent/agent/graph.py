from collections.abc import Callable

from langgraph.graph import END, START, StateGraph

from ..skills.base import SKILLS
from ..tools.executor import CommandExecutionError, execute_command, validate_command
from .planner import plan_skill, review_command_result
from .state import AgentState
from .supervisor import select_skill


MAX_COMMAND_ROUNDS = 6
MAX_SKILL_SWITCHES = 4


def create_agent_graph(model, command_runner: Callable = execute_command):
    def progress(message: str) -> None:
        print(f"  [Progress] {message}", flush=True)

    def intake(state: AgentState):
        question = state.get("original_question", "").strip()
        return {
            "original_question": question,
            "remaining_goal": question,
            "command_results": [],
            "completed_work": [],
            "attempted_skills": [],
            "command_rounds": 0,
            "skill_switches": 0,
            "answer_streamed": False,
            "error": "" if question else "Enter a task to complete",
        }

    def route_skill(state: AgentState):
        progress("Selecting a skill for the remaining goal...")
        try:
            decision = select_skill(
                model,
                state["original_question"],
                state.get("remaining_goal", ""),
                state.get("completed_work", []),
                state.get("attempted_skills", []),
            )
        except Exception as exc:
            return {"error": f"Skill routing failed: {exc}"}

        progress(
            f"Selected skill: {decision.skill_name}, working task: {decision.task}"
        )
        return {
            "selected_skill": decision.skill_name,
            "task": decision.task,
            "confidence": decision.confidence,
        }

    def validate_route(state: AgentState):
        if state.get("error"):
            return {}
        skill_name = state.get("selected_skill", "")
        if skill_name == "unsupported":
            return {"error": "No skill can complete the current goal"}
        if skill_name not in SKILLS:
            return {"error": f"The model selected an unregistered skill: {skill_name}"}
        if state.get("confidence", 0) < 0.3:
            return {"error": "Unable to reliably determine which skill to use"}
        attempted = [*state.get("attempted_skills", [])]
        if skill_name not in attempted:
            attempted.append(skill_name)
        return {"attempted_skills": attempted, "command_rounds": 0}

    def route_after_validation(state: AgentState):
        return "error_reply" if state.get("error") else "load_and_plan_skill"

    def load_and_plan_skill(state: AgentState):
        skill = SKILLS[state["selected_skill"]]
        progress(f"Reading {skill.document.name} and creating an execution plan...")
        try:
            plan = plan_skill(
                model,
                skill,
                state["original_question"],
                state.get("remaining_goal", state["original_question"]),
                state["task"],
                state.get("command_results", []),
            )
        except Exception as exc:
            return {"error": f"Skill planning failed: {exc}"}
        progress(f"Planned action: {plan.action}, working task: {state['task']}")
        return {"plan": plan.model_dump(), "loaded_instructions": str(skill.document)}

    def validate_plan(state: AgentState):
        if state.get("error"):
            return {}
        plan = state.get("plan", {})
        if plan.get("action") != "run_command":
            return {}
        if state.get("command_rounds", 0) >= MAX_COMMAND_ROUNDS:
            return {"error": "The current skill exceeded the command execution limit"}

        command = plan.get("command")
        if not command:
            return {"error": "The execution plan is missing command"}
        try:
            validate_command(command)
        except CommandExecutionError as exc:
            return {"error": str(exc)}
        return {}

    def route_plan(state: AgentState):
        if state.get("error"):
            return "error_reply"
        action = state.get("plan", {}).get("action")
        return {
            "run_command": "execute_command",
            "final_answer": "final_reply",
            "ask_user": "ask_user_reply",
            "reroute_skill": "prepare_reroute",
        }.get(action, "error_reply")

    def run_command(state: AgentState):
        plan = state["plan"]
        command = plan["command"]
        progress(f"Executing command: {command}")
        result = command_runner(command)
        if not (result.success and result.output.get("streamed")):
            progress(f"Command execution {'succeeded' if result.success else 'failed'}")
        return {
            "command_results": [
                *state.get("command_results", []),
                result.model_dump(),
            ],
            "command_rounds": state.get("command_rounds", 0) + 1,
        }

    def review_result(state: AgentState):
        latest = state["command_results"][-1]
        if not latest.get("success"):
            return {
                "error": f"Command execution failed: {latest.get('error', 'unknown error')}"
            }

        output = latest.get("output", {})
        response = output.get("response")
        if isinstance(response, str) and response.strip():
            return {
                "plan": {
                    "action": "final_answer",
                    "answer": response,
                },
                "answer_streamed": bool(output.get("streamed")),
            }
        if output.get("building"):
            return {
                "plan": {
                    "action": "final_answer",
                    "answer": f"The job is currently running, Build #{output.get('build_number', 'unknown')}",
                }
            }
        if output.get("build_result") == "SUCCESS":
            return {
                "plan": {
                    "action": "final_answer",
                    "answer": "The job completed successfully",
                }
            }
        attachment_path = output.get("attachment_path")
        if isinstance(attachment_path, str) and attachment_path.strip():
            remaining_goal = (
                "Analyze the sanitized Jenkins log attachment at "
                f"{attachment_path}. Identify the direct error, root cause, "
                "supporting evidence, fixes, and verification steps."
            )
            return {
                "plan": {
                    "action": "reroute_skill",
                    "remaining_goal": remaining_goal,
                },
                "completed_work": [
                    *state.get("completed_work", []),
                    f"Retrieved the sanitized Jenkins log attachment: {attachment_path}",
                ],
                "remaining_goal": remaining_goal,
            }

        progress("Reviewing whether the current skill completed the goal...")
        try:
            decision = review_command_result(
                model,
                state["original_question"],
                state.get("remaining_goal", state["original_question"]),
                state["task"],
                state["selected_skill"],
                latest,
            )
        except Exception as exc:
            return {"error": f"Command result review failed: {exc}"}

        progress(
            f"Review decision: {decision.decision}, "
            f"remaining goal: {decision.remaining_goal}"
        )
        action = {
            "continue_current_skill": "continue_current_skill",
            "reroute_skill": "reroute_skill",
            "complete": "final_answer",
            "ask_user": "ask_user",
        }[decision.decision]
        plan = {
            "action": action,
            "answer": decision.answer,
            "remaining_goal": decision.remaining_goal,
        }
        updates: AgentState = {"plan": plan}
        if decision.completed_work_summary:
            updates["completed_work"] = [
                *state.get("completed_work", []),
                decision.completed_work_summary,
            ]
        if decision.remaining_goal:
            updates["remaining_goal"] = decision.remaining_goal
        return updates

    def route_review(state: AgentState):
        if state.get("error"):
            return "error_reply"
        action = state.get("plan", {}).get("action")
        return {
            "continue_current_skill": "load_and_plan_skill",
            "reroute_skill": "prepare_reroute",
            "final_answer": "final_reply",
            "ask_user": "ask_user_reply",
        }.get(action, "error_reply")

    def prepare_reroute(state: AgentState):
        switches = state.get("skill_switches", 0) + 1
        if switches > MAX_SKILL_SWITCHES:
            return {"error": "The skill switch limit has been exceeded"}
        progress("The current skill cannot complete the goal; returning to routing")
        plan = state.get("plan", {})
        return {
            "skill_switches": switches,
            "selected_skill": "",
            "task": "",
            "plan": {},
            "remaining_goal": plan.get("remaining_goal")
            or state.get("remaining_goal", state["original_question"]),
            "error": "",
        }

    def route_reroute(state: AgentState):
        return "error_reply" if state.get("error") else "route_skill"

    def final_reply(state: AgentState):
        answer = state.get("plan", {}).get("answer")
        return {"final_answer": answer or "The task completed without an answer"}

    def ask_user_reply(state: AgentState):
        answer = state.get("plan", {}).get("answer")
        return {"final_answer": answer or "More information is required to continue"}

    def error_reply(state: AgentState):
        return {"final_answer": state.get("error") or "The agent execution plan is invalid"}

    builder = StateGraph(AgentState)
    builder.add_node("intake", intake)
    builder.add_node("route_skill", route_skill)
    builder.add_node("validate_route", validate_route)
    builder.add_node("load_and_plan_skill", load_and_plan_skill)
    builder.add_node("validate_plan", validate_plan)
    builder.add_node("execute_command", run_command)
    builder.add_node("review_result", review_result)
    builder.add_node("prepare_reroute", prepare_reroute)
    builder.add_node("final_reply", final_reply)
    builder.add_node("ask_user_reply", ask_user_reply)
    builder.add_node("error_reply", error_reply)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "route_skill")
    builder.add_edge("route_skill", "validate_route")
    builder.add_conditional_edges("validate_route", route_after_validation)
    builder.add_edge("load_and_plan_skill", "validate_plan")
    builder.add_conditional_edges("validate_plan", route_plan)
    builder.add_edge("execute_command", "review_result")
    builder.add_conditional_edges("review_result", route_review)
    builder.add_conditional_edges("prepare_reroute", route_reroute)
    for terminal_node in ("final_reply", "ask_user_reply", "error_reply"):
        builder.add_edge(terminal_node, END)
    return builder.compile()