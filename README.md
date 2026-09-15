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

To enable **Send Mail**, set `MRC_MAIL_SENDER` to the sender mailbox. The Azure
application configured by the existing MRC tenant, client ID, and PFX settings
must have Microsoft Graph `Mail.Send` application permission with admin consent.
The application can be restricted to approved mailboxes with an Exchange
application access policy.

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
python -m mrc_automation_agent.main --cycle 2026WW38 --reminder-type manual
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

`Enable Automation` currently persists the setting and disables manual MRC
controls; it does not start a scheduler. A future scheduler should use the
configured `mrc_automation_settings.timezone` and apply these rules:

- Tuesday and Thursday: scan and download the next reporting week's Excel files,
	then email all owners.
- Monday: scan and download the current reporting week's Excel files, then email
	only owners with missing updates.
- Other days: do nothing. Automated reminders do not generate PPTs.
