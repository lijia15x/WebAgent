import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from web.backend.mrc_service import MrcBusyError, MrcRun, MrcService


class FakeDatabase:
    rows = []
    updates = []

    def get_sendable_drafts(self, cycle_code, include_all):
        return self.rows

    def update_delivery_status(self, *arguments):
        self.updates.append(arguments)


class MrcActionTests(unittest.IsolatedAsyncioTestCase):
    async def test_automation_blocks_manual_actions(self) -> None:
        service = MrcService()
        service.get_automation_enabled = AsyncMock(return_value=True)

        with self.assertRaisesRegex(MrcBusyError, "Automation is enabled"):
            await service.submit_ppt("2026WW38")

    async def test_ppt_requires_local_excel(self) -> None:
        service = MrcService()
        run = MrcRun("run", asyncio.Queue())
        with patch("web.backend.mrc_service.list_cycle_artifacts", return_value=[]):
            await service._run_ppt(run, "2026WW38")

        event = await run.events.get()
        self.assertEqual("error", event["type"])
        self.assertIn("scan SharePoint", event["message"])

    async def test_mail_sends_selected_database_drafts_and_updates_status(self) -> None:
        service = MrcService()
        run = MrcRun("run", asyncio.Queue())
        FakeDatabase.rows = [
            {
                "scan_run_id": 42,
                "owner_name": "Alex",
                "owner_email": "alex@example.com",
                "subject": "Reminder",
                "body_html": "<p>Update</p>",
                "project_count": 2,
            }
        ]
        FakeDatabase.updates = []
        with (
            patch("web.backend.mrc_service.MrcDatabase", FakeDatabase),
            patch("web.backend.mrc_service.GraphEmailSender") as sender_type,
        ):
            sender_type.return_value.send = Mock()
            await service._run_mail(run, "2026WW38", False)

        events = []
        while not run.events.empty():
            events.append(await run.events.get())
        self.assertEqual("completed", events[-1]["type"])
        self.assertEqual(1, events[-1]["sent"])
        self.assertEqual((42, "alex@example.com", "sending"), FakeDatabase.updates[0])
        self.assertEqual((42, "alex@example.com", "sent"), FakeDatabase.updates[1])


if __name__ == "__main__":
    unittest.main()