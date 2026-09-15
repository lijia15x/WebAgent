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
