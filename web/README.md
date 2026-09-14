# Agent Desk Web

The Web application serves the static frontend and a FastAPI API for the
Jenkins Log Analyst. It keeps no conversation history or database state.
Refreshing the page clears the visible conversation.

```text
web/
├── backend/       # FastAPI application
├── frontend/      # HTML, CSS, and JavaScript
├── requirements.txt
└── README.md
```

Install dependencies from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\web\requirements.txt
```

Start one Uvicorn worker:

```powershell
.\.venv\Scripts\python.exe -m uvicorn web.backend.app:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`. Do not use multiple workers because the current
single-task lock is process-local.