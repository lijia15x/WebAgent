import re
from pathlib import Path

from .models import MrcArtifact, WorkbookFile


WORKSPACE_ROOT = Path(__file__).resolve().parent / "workspace"
KINDS = {"excel": ".xlsx", "ppt": ".pptx"}


def _validate_cycle(cycle_code: str) -> str:
    if not re.fullmatch(r"\d{4}WW(?:0[1-9]|[1-4]\d|5[0-3])", cycle_code):
        raise ValueError("Invalid MRC cycle code")
    return cycle_code


def safe_file_name(file_name: str, expected_suffix: str) -> str:
    if Path(file_name).name != file_name or file_name in {"", ".", ".."}:
        raise ValueError("Invalid artifact file name")
    cleaned = re.sub(r"[^A-Za-z0-9._()' -]", "_", file_name).strip(" .")
    if not cleaned or Path(cleaned).suffix.lower() != expected_suffix:
        raise ValueError(f"Artifact must use the {expected_suffix} extension")
    return cleaned


def store_workbooks(
    cycle_code: str,
    workbooks: list[WorkbookFile],
) -> list[MrcArtifact]:
    cycle_dir = WORKSPACE_ROOT / _validate_cycle(cycle_code) / "excel"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for workbook in workbooks:
        file_name = safe_file_name(workbook.name, ".xlsx")
        file_path = cycle_dir / file_name
        file_path.write_bytes(workbook.content)
        artifacts.append(
            MrcArtifact(
                kind="excel",
                file_name=file_name,
                relative_path=file_path.relative_to(WORKSPACE_ROOT).as_posix(),
                modified_time=workbook.modified_time,
                source_url=workbook.source_url,
            )
        )
    return artifacts


def register_ppt(
    cycle_code: str,
    file_path: Path,
    source_workbook_name: str,
) -> MrcArtifact:
    expected_dir = (WORKSPACE_ROOT / _validate_cycle(cycle_code) / "ppt").resolve()
    resolved_path = file_path.resolve()
    if resolved_path.parent != expected_dir or resolved_path.suffix.lower() != ".pptx":
        raise ValueError("PPT artifact is outside the cycle workspace")
    return MrcArtifact(
        kind="ppt",
        file_name=resolved_path.name,
        relative_path=resolved_path.relative_to(WORKSPACE_ROOT.resolve()).as_posix(),
        source_workbook_name=source_workbook_name,
    )


def list_cycle_artifacts(cycle_code: str) -> list[MrcArtifact]:
    cycle = _validate_cycle(cycle_code)
    artifacts = []
    for kind, suffix in KINDS.items():
        artifact_dir = WORKSPACE_ROOT / cycle / kind
        if not artifact_dir.is_dir():
            continue
        for file_path in sorted(artifact_dir.glob(f"*{suffix}")):
            artifacts.append(
                MrcArtifact(
                    kind=kind,
                    file_name=file_path.name,
                    relative_path=file_path.relative_to(WORKSPACE_ROOT).as_posix(),
                )
            )
    return artifacts


def resolve_artifact(cycle_code: str, kind: str, file_name: str) -> Path:
    cycle = _validate_cycle(cycle_code)
    suffix = KINDS.get(kind)
    if suffix is None:
        raise ValueError("Unsupported artifact kind")
    safe_name = safe_file_name(file_name, suffix)
    artifact_dir = (WORKSPACE_ROOT / cycle / kind).resolve()
    file_path = (artifact_dir / safe_name).resolve()
    if file_path.parent != artifact_dir:
        raise ValueError("Artifact path escapes the cycle workspace")
    return file_path