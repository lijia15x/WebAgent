import re


ANSI_ESCAPE = re.compile(r"\x1b(?:[@-_]|\[[0-?]*[ -/]*[@-~])")
SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*)([^\s]+)"),
    re.compile(r"(?i)((?:password|passwd|token|api[_-]?key)\s*[:=]\s*)([^\s]+)"),
    re.compile(r"(?i)(cookie\s*[:=]\s*)([^\r\n]+)"),
)


def sanitize_log(log: str) -> str:
    cleaned = ANSI_ESCAPE.sub("", log)
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub(r"\1[REDACTED]", cleaned)
    return cleaned