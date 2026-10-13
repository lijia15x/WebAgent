import os
import re
from pathlib import Path
from typing import Any, Sequence

import yaml

from common.skills.copilot_sdk.copilot_sdk_client import ask_copilot


ALLOWED_TOP_LEVEL_KEYS = {"version", "boards", "elements", "connections"}
ID_PATTERN = re.compile(r"^[a-z0-9_]+$")


class YamlGenerationError(RuntimeError):
    pass


def build_generation_prompt(source_name: str, reference_names: Sequence[str]) -> str:
    references = ", ".join(reference_names)
    return f"""Convert Figure 12-7, "Johnson City Modular SMBus architecture", from the attached source PDF, {source_name}, into a compliant board-level I2C/I3C architecture YAML file.

The source PDF is authoritative for architecture content and scope. Extract the complete architecture shown in Figure 12-7, not a single bus path or a subset of the figure.

The other attached files ({references}) are normative authoring and representation references. Follow their YAML schema, field choices, ID conventions, connection modeling, ordering conventions, and level of detail. An existing architecture YAML reference, including a .yml, .yaml, or YAML-formatted .txt file, is an example of how to represent the diagram; it is not authoritative for content scope. Do not copy its limited topology or stop at its SMB_MPIC / SMB C[10] path. Add every source-supported board, element, port, and connection needed to represent the complete Figure 12-7 architecture.

Output requirements:
- Return YAML only. Do not use Markdown fences, prose, JSON, or an explanation.
- Use exactly these top-level keys in this order: version, boards, elements, connections.
- Set version to 1.
- Include all board and module boundaries, SMBus/I2C/I3C controllers, hubs, muxes, buffers, translators, connectors, cables, and endpoint devices visibly represented in Figure 12-7.
- Include every visible bus branch in Figure 12-7, including all source-supported AST2600 SMB and I3C controller paths; do not limit extraction to SMB_MPIC / SMB C[10].
- Model each physical or logical hop as a separate connection.
- Use lowercase snake_case for generated IDs. Board and element IDs must be globally unique where required; port IDs must be unique within their element.
- Every element.board must resolve to a declared board.
- Every connection endpoint must resolve to a declared element and one of its declared ports.
- Every port_display_order entry must resolve to a declared port and must not be duplicated.
- Use internal_net, mating, or cable according to the physical relationship described by the source.
- Quote hexadecimal addresses. Use two-space indentation.
- Omit optional values that cannot be established from the source. Do not invent addresses, voltage domains, speeds, cable lengths, part numbers, signals, labels, or electrical roles.
- Do not add source, metadata, review, notes, confidence, or other custom top-level sections.
- Do not add source-page or figure-number tracking unless it already exists in the reference YAML.
- Do not broaden the result beyond Figure 12-7 into Figure 12-6, Figure 12-8, or other diagrams and sections in the PDF.

Before responding, silently verify the complete output against the normative guide, including all IDs and connection references."""


def strip_yaml_fence(content: str) -> str:
    cleaned = content.strip()
    match = re.fullmatch(r"```(?:ya?ml)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else cleaned


def validate_architecture_yaml(content: str) -> dict[str, Any]:
    checks = {
        "schema": {"valid": True, "detail": "Required sections and fields are valid"},
        "references": {"valid": True, "detail": "Board, port, and connection references resolve"},
        "unique_ids": {"valid": True, "detail": "Board, element, and port IDs are unique"},
    }
    errors: list[str] = []

    def fail(check: str, message: str) -> None:
        checks[check]["valid"] = False
        errors.append(message)

    try:
        document = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        fail("schema", f"Invalid YAML syntax: {exc}")
        return {"valid": False, "checks": checks, "errors": errors}

    if not isinstance(document, dict):
        fail("schema", "The YAML root must be a mapping")
        return {"valid": False, "checks": checks, "errors": errors}

    keys = set(document)
    missing_keys = ALLOWED_TOP_LEVEL_KEYS - keys
    extra_keys = keys - ALLOWED_TOP_LEVEL_KEYS
    if missing_keys:
        fail("schema", f"Missing top-level keys: {', '.join(sorted(missing_keys))}")
    if extra_keys:
        fail("schema", f"Unsupported top-level keys: {', '.join(sorted(extra_keys))}")
    if document.get("version") != 1:
        fail("schema", "version must be the integer 1")

    boards = document.get("boards")
    elements = document.get("elements")
    connections = document.get("connections")
    for key, value in (("boards", boards), ("elements", elements), ("connections", connections)):
        if not isinstance(value, list):
            fail("schema", f"{key} must be a list")
    if not all(isinstance(value, list) for value in (boards, elements, connections)):
        return {"valid": False, "checks": checks, "errors": errors}
    if not boards:
        fail("schema", "boards must contain at least one board")
    if not elements:
        fail("schema", "elements must contain at least one element")

    board_ids: set[str] = set()
    for board in boards:
        if not isinstance(board, dict):
            fail("schema", "Each board must be a mapping")
            continue
        board_id = board.get("id")
        if not isinstance(board_id, str) or not ID_PATTERN.fullmatch(board_id):
            fail("schema", "Each board id must use lowercase snake_case")
        elif board_id in board_ids:
            fail("unique_ids", f"Duplicate board id: {board_id}")
        else:
            board_ids.add(board_id)
        if not isinstance(board.get("label"), str) or not board["label"].strip():
            fail("schema", f"Board {board_id or '<unknown>'} requires a label")

    element_ids: set[str] = set()
    element_ports: dict[str, set[str]] = {}
    for element in elements:
        if not isinstance(element, dict):
            fail("schema", "Each element must be a mapping")
            continue
        element_id = element.get("id")
        if not isinstance(element_id, str) or not ID_PATTERN.fullmatch(element_id):
            fail("schema", "Each element id must use lowercase snake_case")
            continue
        if element_id in element_ids:
            fail("unique_ids", f"Duplicate element id: {element_id}")
        element_ids.add(element_id)
        if element.get("board") not in board_ids:
            fail("references", f"Element {element_id} references unknown board {element.get('board')}")
        if not isinstance(element.get("type"), str) or not element["type"].strip():
            fail("schema", f"Element {element_id} requires a type")
        if "address" in element and not isinstance(element["address"], str):
            fail("schema", f"Element {element_id} address must be quoted as a string")
        ports = element.get("ports")
        if not isinstance(ports, list) or not ports:
            fail("schema", f"Element {element_id} requires at least one port")
            element_ports[element_id] = set()
            continue
        port_ids: set[str] = set()
        for port in ports:
            port_id = port.get("id") if isinstance(port, dict) else None
            if not isinstance(port_id, str) or not port_id:
                fail("schema", f"Element {element_id} contains a port without an id")
            elif port_id in port_ids:
                fail("unique_ids", f"Element {element_id} has duplicate port id {port_id}")
            else:
                port_ids.add(port_id)
        element_ports[element_id] = port_ids
        display_order = element.get("port_display_order")
        if display_order is not None:
            if not isinstance(display_order, list):
                fail("schema", f"Element {element_id} port_display_order must be a list")
            elif len(display_order) != len(set(display_order)) or any(port_id not in port_ids for port_id in display_order):
                fail("references", f"Element {element_id} has an invalid port_display_order")

    for connection in connections:
        if not isinstance(connection, dict):
            fail("schema", "Each connection must be a mapping")
            continue
        for field in ("from", "from_port", "to", "to_port", "connection_type"):
            if not isinstance(connection.get(field), str) or not connection[field]:
                fail("schema", f"Connection requires {field}")
        connection_type = connection.get("connection_type")
        if not isinstance(connection_type, str) or connection_type not in {"internal_net", "mating", "cable"}:
            fail("schema", f"Unsupported connection_type: {connection_type}")
        for endpoint, port_key in (("from", "from_port"), ("to", "to_port")):
            element_id = connection.get(endpoint)
            port_id = connection.get(port_key)
            if element_id not in element_ports:
                fail("references", f"Connection references unknown element {element_id}")
            elif port_id not in element_ports[element_id]:
                fail("references", f"Connection references unknown port {element_id}.{port_id}")

    for name, check in checks.items():
        if not check["valid"]:
            count = sum(1 for error in errors if name.replace("_ids", "") in error.lower())
            check["detail"] = f"Validation failed; review {max(count, 1)} issue(s)"
    return {"valid": not errors, "checks": checks, "errors": errors}


def build_repair_prompt(candidate: str, errors: Sequence[str]) -> str:
    issues = "\n".join(f"- {error}" for error in errors)
    return f"""Repair the YAML candidate below so it complies with the attached source PDF and normative references.

Validator findings:
{issues}

Candidate:
```yaml
{candidate}
```

Return the complete corrected YAML only, without Markdown fences or explanation. Preserve the complete Figure 12-7 Johnson City Modular SMBus architecture, not only the SMB_MPIC / SMB C[10] path. Preserve source-supported architecture facts, do not invent missing facts, and use exactly the top-level keys version, boards, elements, connections."""


async def generate_architecture_yaml(
    source_pdf: Path,
    reference_files: Sequence[Path],
    model: str | None = None,
) -> tuple[str, dict[str, Any]]:
    attachments = [source_pdf, *reference_files]
    prompt = build_generation_prompt(source_pdf.name, [path.name for path in reference_files])
    content = await ask_copilot(
        prompt,
        model=model or os.getenv("PDF_YAML_MODEL", "gpt-5.6-sol"),
        files=attachments,
        workspace="",
        timeout=600.0,
    )
    candidate = strip_yaml_fence(content)
    validation = validate_architecture_yaml(candidate)
    if validation["valid"]:
        return candidate, validation

    repaired = await ask_copilot(
        build_repair_prompt(candidate, validation["errors"]),
        model=model or os.getenv("PDF_YAML_MODEL", "gpt-5.6-sol"),
        files=attachments,
        workspace="",
        timeout=600.0,
    )
    candidate = strip_yaml_fence(repaired)
    validation = validate_architecture_yaml(candidate)
    if not validation["valid"]:
        raise YamlGenerationError(
            "Copilot returned non-compliant YAML after one repair attempt: "
            + "; ".join(validation["errors"][:5])
        )
    return candidate, validation