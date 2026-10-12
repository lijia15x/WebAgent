from datetime import datetime, timezone
from pathlib import Path


REFERENCE_WORKSPACE = Path(__file__).resolve().parent / "workspace" / "reference_files"
ALLOWED_REFERENCE_SUFFIXES = {".md", ".pdf", ".txt", ".yaml", ".yml"}


class InvalidReferenceFile(ValueError):
    pass


def normalize_reference_name(file_name: str | None) -> str:
    name = (file_name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name or name in {".", ".."}:
        raise InvalidReferenceFile("Reference file name is invalid")
    if Path(name).suffix.lower() not in ALLOWED_REFERENCE_SUFFIXES:
        raise InvalidReferenceFile(
            "Only Markdown, PDF, YAML, and text reference files are supported"
        )
    return name


def resolve_reference(file_name: str) -> Path:
    name = normalize_reference_name(file_name)
    workspace = REFERENCE_WORKSPACE.resolve()
    candidate = (workspace / name).resolve()
    if candidate.parent != workspace:
        raise InvalidReferenceFile("Reference file path is invalid")
    return candidate


def ensure_reference_workspace() -> Path:
    REFERENCE_WORKSPACE.mkdir(parents=True, exist_ok=True)
    return REFERENCE_WORKSPACE


def list_reference_paths() -> list[Path]:
    workspace = ensure_reference_workspace()
    return sorted(
        (
            path
            for path in workspace.iterdir()
            if path.is_file()
            and not path.is_symlink()
            and path.suffix.lower() in ALLOWED_REFERENCE_SUFFIXES
        ),
        key=lambda path: path.name.casefold(),
    )


def list_references() -> list[dict[str, object]]:
    return [
        {
            "name": path.name,
            "size": path.stat().st_size,
            "modified_at": datetime.fromtimestamp(
                path.stat().st_mtime, timezone.utc
            ).isoformat(),
        }
        for path in list_reference_paths()
    ]


def delete_reference(file_name: str) -> bool:
    path = resolve_reference(file_name)
    if not path.is_file() or path.is_symlink():
        return False
    path.unlink()
    return True