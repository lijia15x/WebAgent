import unittest

from .copilot_sdk_client import _message_is_process


class MessageClassificationTests(unittest.TestCase):
    def test_reasoning_phase_is_process(self) -> None:
        self.assertTrue(_message_is_process("reasoning", False))

    def test_tool_request_message_is_process(self) -> None:
        self.assertTrue(_message_is_process(None, True))

    def test_unmarked_final_message_is_answer(self) -> None:
        self.assertFalse(_message_is_process(None, False))


if __name__ == "__main__":
    unittest.main()