# MRC Automation Agent

This agent runs a fixed LangGraph workflow. It does not use an LLM, skill router, or planner.

```text
prepare_cycle
  -> create_scan
  -> fetch_sharepoint
  -> parse_workbooks
  -> select_recipients
  -> build_drafts
  -> persist_snapshot
```

The current implementation scans SharePoint workbooks, stores a MySQL snapshot, and creates one email draft per owner. It does not send email.

## MySQL 8.4

Run the SQL files with an administrator account:

```powershell
mysql -u root -p < mrc_automation_agent/mysql/001_create_database.sql
mysql -u root -p webagent < mrc_automation_agent/mysql/002_create_tables.sql
```

Copy `.env.example` to `.env` in this directory and set the MySQL and SharePoint credentials. The agent loads this file automatically without overriding variables already set in the process environment. The MRC variables use the `MRC_` prefix and do not conflict with the Jenkins agent's separate `log_analysis_agent/.env` file.

## Dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r mrc_automation_agent\requirements.txt
```

## Test

The graph tests use in-memory fakes and do not access MySQL or SharePoint:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s mrc_automation_agent\tests -v
```

## Run a scan

After configuring the environment and creating the MySQL tables:

```powershell
.\.venv\Scripts\python.exe -m mrc_automation_agent.main --cycle 2026WW38
```

Use `--reminder-type monday` to create drafts only for owners who have at least one missing status update. Tuesday and Thursday modes create one draft for every owner.

## Web API

- `POST /api/agents/mrc-automation/scans`
- `GET /api/agents/mrc-automation/cycles/{cycle_code}/latest`
- `GET /api/agents/mrc-automation/automation`
- `PUT /api/agents/mrc-automation/automation`
- `GET /api/runs/{run_id}/events`