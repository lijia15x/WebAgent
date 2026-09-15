import unittest

from log_analysis_agent.agent.skill_registry import SKILLS
from log_analysis_agent.tools.executor import (
    ALLOWED_SKILL_MODULES,
    CommandExecutionError,
    parse_command,
)


class SkillAccessTests(unittest.TestCase):
    def test_jenkins_agent_exposes_only_its_registered_skills(self) -> None:
        self.assertEqual({"jenkins_api", "copilot_sdk"}, set(SKILLS))
        for skill in SKILLS.values():
            self.assertIn("common/skills", skill.document.as_posix())
            self.assertTrue(skill.document.is_file())

    def test_executor_allows_only_jenkins_agent_modules(self) -> None:
        expected_modules = {
            "common.skills.jenkins_api.get_job_status",
            "common.skills.jenkins_api.get_console_log",
            "common.skills.copilot_sdk.run_copilot",
        }
        self.assertEqual(expected_modules, set(ALLOWED_SKILL_MODULES))

        for module in expected_modules:
            arguments = parse_command(f"python -m {module} --help")
            self.assertEqual(module, arguments[2])

        rejected_modules = {
            "common.skills.jenkins_api.client",
            "common.skills.unrelated.run",
            "log_analysis_agent.skills.jenkins_api.get_job_status",
        }
        for module in rejected_modules:
            with self.subTest(module=module):
                with self.assertRaises(CommandExecutionError):
                    parse_command(f"python -m {module}")


if __name__ == "__main__":
    unittest.main()