# Log Analysis Agent

A general LangGraph agent that uses Ollama to select a Markdown skill, plan
documented Python commands, review their results, and switch skills until the
user's goal is complete.

## Skill layout

The `skills` package is next to `agent`. Each skill is self-contained under
`skills/<skill_name>/`:

```text
log_analysis_agent/
├── agent/
├── skills/
│   ├── jenkins_api/
│   │   ├── SKILL.md
│   │   ├── client.py
│   │   ├── get_job_status.py
│   │   ├── get_console_log.py
│   │   └── log_sanitizer.py
│   └── copilot_sdk/
│       ├── SKILL.md
│       ├── copilot_sdk_client.py
│       └── run_copilot.py
├── tools/
├── main.py
└── requirements.txt
```

`SKILL.md` describes when and how the skill is used. The Python files in the
same directory implement that skill. Shared registration infrastructure stays
in `skills/base.py`.

The execution lifecycle is:

```text
route skill -> load SKILL.md -> plan -> validate -> execute command
									  ^                 |
									  +---- review -----+
```

The review step may continue the current skill, finish the task, ask the user,
or return to the router to select another skill. A skill documents executable
Python module commands. Node 3 runs them without a shell and accepts only modules
under `log_analysis_agent.skills`.

Copilot and Claude skill documents can use the same directory convention. Their
commands must be implemented as Python modules inside the skill package and must
print one JSON object to standard output.

## Install

From the repository root, create or activate the virtual environment and install
the pinned dependencies. Use the corporate proxy when direct PyPI access is not
available:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\log_analysis_agent\requirements.txt --proxy http://child-prc.intel.com:913
```

## Configuration

Set the values in `.env`. The application loads this file automatically. Do not
commit real API tokens. The Jenkins account only needs read access to jobs,
builds, and logs.

Example:

```dotenv
OLLAMA_BASE_URL=http://10.112.230.27:11434
OLLAMA_MODEL=qwen3:32b
JENKINS_USERNAME=your-username
JENKINS_API_TOKEN=your-api-token
```

`OLLAMA_BASE_URL` must point to a reachable Ollama server, and the configured
model must already exist on that server. Authenticate GitHub Copilot before using
the `copilot_sdk` skill.

### Windows environment variables

When Ollama and Jenkins are on the internal network but GitHub Copilot requires
the corporate proxy, set the proxy for external traffic and bypass it for Intel
hosts and the Ollama server.

Set variables for the current PowerShell session before starting the agent:

```powershell
$env:HTTP_PROXY = "http://child-prc.intel.com:913"
$env:HTTPS_PROXY = "http://child-prc.intel.com:913"
$env:NO_PROXY = "intel.com,.intel.com,10.112.230.27,localhost,127.0.0.1"
$env:no_proxy = $env:NO_PROXY
```

To persist the same variables for the current Windows user:

```powershell
[Environment]::SetEnvironmentVariable(
	"HTTP_PROXY",
	"http://child-prc.intel.com:913",
	"User"
)
[Environment]::SetEnvironmentVariable(
	"HTTPS_PROXY",
	"http://child-prc.intel.com:913",
	"User"
)
[Environment]::SetEnvironmentVariable(
	"NO_PROXY",
	"intel.com,.intel.com,10.112.230.27,localhost,127.0.0.1",
	"User"
)
[Environment]::SetEnvironmentVariable(
	"no_proxy",
	"intel.com,.intel.com,10.112.230.27,localhost,127.0.0.1",
	"User"
)
```

Replace `10.112.230.27` when `OLLAMA_BASE_URL` uses another host. Close and
restart VS Code after setting persistent variables. Some HTTP clients do not
support CIDR entries in `NO_PROXY`, so list the exact Ollama host whenever
possible.

## Run

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m log_analysis_agent.main
```

Enter a natural-language task or a classic Jenkins job/build URL. The CLI shows
public routing and tool progress but does not expose model reasoning, credentials,
or raw logs.