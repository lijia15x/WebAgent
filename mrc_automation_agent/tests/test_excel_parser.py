import unittest
from io import BytesIO

from openpyxl import Workbook

from mrc_automation_agent.excel_parser import parse_workbook
from mrc_automation_agent.models import WorkbookFile


class ExcelParserTests(unittest.TestCase):
    def test_finds_status_comments_by_header_in_column_l(self) -> None:
        excel = Workbook()
        sheet = excel.active
        sheet.title = "Weekly Status"
        sheet.append(["MRC weekly report"])
        headers = [None] * 12
        headers[1] = "Function Team"
        headers[3] = "Project Name"
        headers[6] = "Owner"
        headers[8] = "Owner Email"
        headers[11] = "Status Comments"
        sheet.append(headers)
        values = [None] * 12
        values[1] = "Core Platform"
        values[3] = "Atlas Migration"
        values[6] = "Alex Kim"
        values[8] = "Alex.Kim@example.com"
        values[11] = "On track"
        sheet.append(values)
        content = BytesIO()
        excel.save(content)

        records = parse_workbook(
            WorkbookFile("MRC.xlsx", "https://example.invalid/MRC.xlsx", content.getvalue()),
            header_search_rows=5,
        )

        self.assertEqual(1, len(records))
        self.assertEqual("Weekly Status", records[0].sheet_name)
        self.assertEqual("alex.kim@example.com", records[0].owner_email)
        self.assertEqual("On track", records[0].status_comments)


if __name__ == "__main__":
    unittest.main()