from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    description: str
    document: Path

    def instructions(self) -> str:
        return self.document.read_text(encoding="utf-8")


SKILLS_DIR = Path(__file__).resolve().parents[2] / "common" / "skills"

SKILLS = {
    "jenkins_api": SkillDefinition(
        name="jenkins_api",
        description=(
            "Query Jenkins job or build status and retrieve sanitized console logs "
            "through project Python scripts."
        ),
        document=SKILLS_DIR / "jenkins_api" / "SKILL.md",
    ),
    "copilot_sdk": SkillDefinition(
        name="copilot_sdk",
        description=(
            "Analyze sanitized build logs by sending a prompt and log attachment "
            "to GitHub Copilot SDK."
        ),
        document=SKILLS_DIR / "copilot_sdk" / "SKILL.md",
    ),
}


def skill_index() -> list[dict[str, str]]:
    return [
        {"name": skill.name, "description": skill.description}
        for skill in SKILLS.values()
    ]