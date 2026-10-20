# WebAgent

## Quick start

Requirements: Python 3.14 and access to MySQL 8.4.

Run the following commands in Windows PowerShell from the repository root:

```powershell
# 1. Create and activate the Python virtual environment
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

# 2. Install all project dependencies
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt

# 3. Create the local configuration file
Copy-Item .\.env.example .\.env
```

Fill in the required values in `.env`. The file is shared by all agents and is
ignored by Git.

`LOG_ANALYSIS_MODEL` controls the GitHub Copilot model used by Jenkins log
analysis. `MRC_PPT_MODEL` independently controls the model used for MRC PPT
generation.

To enable **Send Mail**, configure `MRC_SMTP_SENDER_EMAIL`,
`MRC_SMTP_SENDER_PASSWORD`, `MRC_SMTP_SERVER`, and `MRC_SMTP_PORT`. The MRC
service connects with SMTP AUTH, upgrades the connection using STARTTLS, and
sends the generated HTML reminder through the authenticated mailbox.

If MRC Automation will be used and its tables do not exist yet, install the
MySQL command-line client, add `mysql` to `PATH`, and initialize the database
once:

```powershell
mysql -u root -p -e "source mrc_automation_agent/mysql/001_create_database.sql"
mysql -u root -p webagent -e "source mrc_automation_agent/mysql/002_create_tables.sql"
```

Start the Web application:

```powershell
python -m uvicorn web.backend.app:app --host 0.0.0.0 --port 8000
```

Open <http://127.0.0.1:8000>.

## Run an agent directly

Start the Jenkins Log Analysis Agent:

```powershell
python .\log_analysis_agent\main.py
```

Run one MRC Automation scan:

```powershell
python -m mrc_automation_agent.main --cycle 2026WW38 --reminder-type reminder
```

The Web UI exposes three independent manual actions: **Scan SharePoint** downloads
the selected cycle's Excel files and prepares owner data, **Send Mail** sends to
missing owners or all owners, and **Generate PPT** uses the locally downloaded
Excel files. Generate PPT and Send Mail require a successful scan first.

Downloaded Excel files and generated PPTs are stored under
`mrc_automation_agent/workspace/<cycle>/` and are available for download from
the MRC page. Each weekly Excel workbook produces its own PPT.
Configure the AI model with `MRC_PPT_MODEL` in `.env` when the default is not
suitable; the project uses its bundled MRC PowerPoint template.

MRC PPT calls also accept `MRC_PPT_REASONING_EFFORT` (default `high`; choices:
`low`, `medium`, `high`, `xhigh`, `max`) and `MRC_PPT_CONTEXT_TIER` (default
`default`; choices: `default`, `long_context`). The latter selects a context
tier, not a numeric token limit. Both settings apply to slides 2 and 3 for all
MRC templates. Empty values use the defaults; invalid values fail configuration
validation. Model support for each tier depends on the Copilot service.
Restart the backend after changing environment settings.

Workbooks whose filenames contain `DMR-16ch` (case-insensitive) use the dedicated
pre-read dashboard template and prompts. Slide 2 contains Highlights, grouped
engineering updates, up to five sourced milestones, per-item **Details** links,
and a full-workbook link. Targets, forecasts, actual dates and worst-case dates
remain distinct; absent dates display `Not provided`. Slide 3 provides concise
supporting detail without padding each group to a fixed number of paragraphs.
Other workbooks retain their existing prompts and template behavior.

DMR-16ch generation validates that cited cells exist and are nonblank, that each
milestone date occurs in its cited cell, and that content stays within the
dashboard's item and text limits. Date matching tolerates equivalent quote,
spacing and dash styles, but does not infer years or substitute different dates.
When content validation fails, only the failing slide is regenerated with the
specific validation error, for at most three attempts. Persistent failures stop
generation rather than silently dropping content or retaining template placeholders. These checks
do not replace a factual review of the model's narrative or date classification.
Links use the downloaded artifact's source URL, never a model-provided URL; when
no source URL is available, no clickable links are fabricated.

`Enable Automation` currently persists the setting and disables manual MRC
controls; it does not start a scheduler. A future scheduler should use the
configured `mrc_automation_settings.timezone` and apply these rules:

- Tuesday and Thursday: scan and download the next reporting week's Excel files,
	then email all owners.
- Monday: scan and download the current reporting week's Excel files, then email
	only owners with missing updates.
- Other days: do nothing. Automated reminders do not generate PPTs.
