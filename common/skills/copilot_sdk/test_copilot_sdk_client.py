import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from .copilot_sdk_client import _message_is_process, ask_copilot


class MessageClassificationTests(unittest.TestCase):
    def test_reasoning_phase_is_process(self) -> None:
        self.assertTrue(_message_is_process("reasoning", False))

    def test_tool_request_message_is_process(self) -> None:
        self.assertTrue(_message_is_process(None, True))

    def test_unmarked_final_message_is_answer(self) -> None:
        self.assertFalse(_message_is_process(None, False))


class CopilotSessionSettingsTests(unittest.IsolatedAsyncioTestCase):
    async def test_session_receives_optional_reasoning_and_context(self) -> None:
        session = SimpleNamespace(
            send_and_wait=AsyncMock(
                return_value=SimpleNamespace(data=SimpleNamespace(content="ok"))
            )
        )
        client = SimpleNamespace(
            start=AsyncMock(),
            create_session=AsyncMock(return_value=session),
            stop=AsyncMock(),
        )
        modules = {
            "copilot": SimpleNamespace(CopilotClient=lambda: client),
            "copilot.session": SimpleNamespace(
                PermissionHandler=SimpleNamespace(approve_all=object())
            ),
            "copilot.session_events": SimpleNamespace(),
        }
        with patch(
            "common.skills.copilot_sdk.copilot_sdk_client.importlib.import_module",
            side_effect=modules.__getitem__,
        ):
            self.assertEqual(
                "ok",
                await ask_copilot(
                    "prompt", reasoning_effort="high", context_tier="long_context"
                ),
            )
            self.assertEqual(
                "high", client.create_session.await_args.kwargs["reasoning_effort"]
            )
            self.assertEqual(
                "long_context", client.create_session.await_args.kwargs["context_tier"]
            )
            self.assertEqual("ok", await ask_copilot("prompt"))
            self.assertIsNone(client.create_session.await_args.kwargs["reasoning_effort"])
            self.assertIsNone(client.create_session.await_args.kwargs["context_tier"])


if __name__ == "__main__":
    unittest.main()