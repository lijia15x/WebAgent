import asyncio
import copy
import json
import os
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Awaitable, Callable, Sequence

import yaml

from common.skills.copilot_sdk.copilot_sdk_client import ask_copilot
from pdf_to_yaml_agent.pdf_filter import (
    ArchitectureFigureNotFoundError,
    ArchitectureSelection,
    extract_architecture_pages,
)


ALLOWED_TOP_LEVEL_KEYS = {"version", "boards", "elements", "connections"}
ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
ProgressCallback = Callable[[str, int], Awaitable[None]]
ActivityCallback = Callable[[str], Awaitable[None]]
ProcessCallback = Callable[[str], Awaitable[None]]
PDF_WORKSPACE_GUIDANCE = """Use the temporary request workspace actively. You may create analysis files and run read-only inspection commands inside it. Do not modify the source PDF or files under references. Do not access files outside this workspace. All analysis artifacts are temporary and must not be mentioned in the final response."""
DEFAULT_GENERATION_TIMEOUT_SECONDS = 900.0
DEFAULT_REPAIR_TIMEOUT_SECONDS = 300.0
REVIEWED_EXAMPLE_DIRECTORY = Path(__file__).resolve().parent / "reference"
REVIEWED_EXAMPLE_PDF = REVIEWED_EXAMPLE_DIRECTORY / "reference.pdf"
REVIEWED_EXAMPLE_YAML = REVIEWED_EXAMPLE_DIRECTORY / "I2C_architecure.yml"


class YamlGenerationError(RuntimeError):
    pass


def reviewed_example_files() -> tuple[Path, Path]:
    missing = [
        path.name
        for path in (REVIEWED_EXAMPLE_PDF, REVIEWED_EXAMPLE_YAML)
        if not path.is_file()
    ]
    if missing:
        raise YamlGenerationError(
            "Reviewed PDF-to-YAML example is incomplete; missing: "
            + ", ".join(missing)
        )
    return REVIEWED_EXAMPLE_PDF, REVIEWED_EXAMPLE_YAML


def select_reference_files(reference_files: Sequence[Path]) -> list[Path]:
    selected: dict[str, Path] = {}
    for path in reference_files:
        key = path.stem.casefold()
        current = selected.get(key)
        if current is None or (path.suffix.lower() == ".md" and current.suffix.lower() == ".pdf"):
            selected[key] = path
    return sorted(selected.values(), key=lambda path: path.name.casefold())


def timeout_from_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        timeout = float(raw_value)
    except ValueError as exc:
        raise YamlGenerationError(f"{name} must be a number of seconds") from exc
    if timeout <= 0:
        raise YamlGenerationError(f"{name} must be greater than zero")
    return timeout


def build_generation_prompt(
    source_name: str,
    reference_names: Sequence[str],
    selection: ArchitectureSelection,
    python_executable: str = "python",
) -> str:
    references = ", ".join(reference_names)
    figures = "\n".join(
        f"- Original PDF page {figure.page_number}: {figure.caption}"
        for figure in selection.figures
    )
    return f"""Convert the selected {selection.product_name} SMBus architecture into a compliant board-level I2C/I3C architecture YAML file.

The attached source, {source_name}, has already been reduced to the selected figure page from the original PDF:
{figures}

The authoritative target is: {selection.target.caption}

The target figure is authoritative for architecture content and scope. A modular SMBus architecture figure is selected when available; otherwise, the selected base SMBus architecture figure is used.

The other attached files ({references}) are authoring and representation references. The Markdown authoring guide is normative for the YAML schema, field choices, ID conventions, connection modeling, and ordering conventions.

The paired files references/reviewed_example/reference.pdf and references/reviewed_example/I2C_architecure.yml are a human-reviewed worked example. The YAML intentionally models only the SMB C[10] path from its paired PDF. Inspect the pair together to learn how visible PDF regions map to boards, how components map to elements and ports, and how each physical or logical hop maps to a connection. Use spatial enclosure, region labels, and connector boundaries to determine board ownership; do not assign an endpoint to a board merely because its bus path connects into that board.

The reviewed pair is authoritative only for representation technique, not for the current architecture's content, IDs, labels, component count, path count, or topology scope. An existing architecture YAML reference is not authoritative for content scope. Do not copy its limited topology or hardware facts, do not stop at SMB C[10] or one example bus path, and do not omit regions or branches just because the reviewed YAML omits paths outside its deliberately limited scope. The current target figure remains the sole authority for what to include. Add every source-supported board, element, port, and connection needed to represent the complete authoritative target figure.

Mandatory command-line agent workflow before the final response:
1. Inspect the workspace files and use `{python_executable}` with PyMuPDF to extract the PDF text layer, page dimensions, figure captions, and visible labels. Do not rely on a whole-page thumbnail alone.
2. Render the authoritative target figure as a high-resolution full image plus overlapping 3x-5x crops covering every diagram region, including controllers, Aggregator or equivalent distribution logic, host modules, system boards, connector arrays, and lower or side detail panels. Inspect every crop.
3. Create an analysis/source_inventory.json file. Inventory every visible board or module, controller, hub, mux, buffer, translator, connector, cable endpoint, target device, address, named port, and source-supported connection. Record the source page and crop for each fact. Connector-only boundaries, reserved channels, optional slots, and internal-only detail diagrams must be identified rather than silently discarded or forced into the main connected component.
4. Build analysis/candidate.yml from that inventory. Then run a local Python audit that parses both source_inventory.json and candidate.yml. The audit must report inventory items and visible branches missing from the candidate, unresolved references, duplicate IDs, active hub or mux downstream ports with no represented destination, and physical distribution layers that were collapsed or bypassed.
5. Return to the relevant crop for every audit finding. Correct source-supported omissions in candidate.yml; do not fabricate destinations that the figure does not show. Repeat the audit until every remaining exception is explicitly supported as reserved, optional, connector-only, or internal-only by the source.
6. Read the final candidate.yml from disk and return that exact YAML as the response. Analysis files are temporary working artifacts, not output fields.

Output requirements:
- Return YAML only. Do not use Markdown fences, prose, JSON, or an explanation.
- Use exactly these top-level keys in this order: version, boards, elements, connections.
- Set version to 1.
- Include all board and module boundaries, SMBus/I2C/I3C controllers, hubs, muxes, buffers, translators, connectors, cables, and endpoint devices visibly represented in the target figure.
- Include every visible bus branch in the target figure; do not limit extraction to a single bus path or to the topology scope of an example YAML.
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
- Do not broaden the result beyond the authoritative target figure. Supporting base figures may clarify shared facts but must not expand or replace the target topology.

Before responding, verify the complete output against both the source inventory and the normative guide, including source coverage, all IDs, and all connection references."""


def strip_yaml_fence(content: str) -> str:
    cleaned = content.strip()
    match = re.fullmatch(r"```(?:ya?ml)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else cleaned


def validate_architecture_yaml(content: str) -> dict[str, Any]:
    checks = {
        "schema": {"valid": True, "detail": "Required sections and fields are valid"},
        "references": {"valid": True, "detail": "Board, port, and connection references resolve"},
        "unique_ids": {"valid": True, "detail": "Board, element, and port IDs are unique"},
        "topology": {"valid": True, "detail": "Architecture topology is connected and complete"},
    }
    errors: list[str] = []
    warnings: list[str] = []
    error_counts: dict[str, int] = defaultdict(int)
    warning_counts: dict[str, int] = defaultdict(int)

    def fail(check: str, message: str) -> None:
        checks[check]["valid"] = False
        error_counts[check] += 1
        errors.append(message)

    def warn(check: str, message: str) -> None:
        checks[check]["valid"] = False
        warning_counts[check] += 1
        warnings.append(message)

    try:
        document = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        fail("schema", f"Invalid YAML syntax: {exc}")
        return {
            "valid": False,
            "review_required": False,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }

    if not isinstance(document, dict):
        fail("schema", "The YAML root must be a mapping")
        return {
            "valid": False,
            "review_required": False,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }

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
        return {
            "valid": False,
            "review_required": False,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }
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
    element_types: dict[str, str] = {}
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
        else:
            element_types[element_id] = element["type"].strip().lower()
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

    valid_connections: list[dict[str, Any]] = []
    for connection in connections:
        if not isinstance(connection, dict):
            fail("schema", "Each connection must be a mapping")
            continue
        connection_valid = True
        for field in ("from", "from_port", "to", "to_port", "connection_type"):
            if not isinstance(connection.get(field), str) or not connection[field]:
                fail("schema", f"Connection requires {field}")
                connection_valid = False
        connection_type = connection.get("connection_type")
        if not isinstance(connection_type, str) or connection_type not in {"internal_net", "mating", "cable"}:
            fail("schema", f"Unsupported connection_type: {connection_type}")
            connection_valid = False
        for endpoint, port_key in (("from", "from_port"), ("to", "to_port")):
            element_id = connection.get(endpoint)
            port_id = connection.get(port_key)
            if not isinstance(element_id, str) or element_id not in element_ports:
                fail("references", f"Connection references unknown element {element_id}")
                connection_valid = False
            elif not isinstance(port_id, str) or port_id not in element_ports[element_id]:
                fail("references", f"Connection references unknown port {element_id}.{port_id}")
                connection_valid = False
        if connection_valid:
            valid_connections.append(connection)

    if element_ids and len(valid_connections) == len(connections):
        adjacency = {element_id: set() for element_id in element_ids}
        port_connection_types: dict[tuple[str, str], set[str]] = defaultdict(set)
        port_usage: dict[tuple[str, str], int] = defaultdict(int)
        for connection in valid_connections:
            source = connection["from"]
            destination = connection["to"]
            adjacency[source].add(destination)
            adjacency[destination].add(source)
            port_connection_types[(source, connection["from_port"])].add(
                connection["connection_type"]
            )
            port_connection_types[(destination, connection["to_port"])].add(
                connection["connection_type"]
            )
            port_usage[(source, connection["from_port"])] += 1
            port_usage[(destination, connection["to_port"])] += 1

        connection_signatures: Counter[tuple[str, str, str, str, str]] = Counter()
        for connection in valid_connections:
            endpoints = sorted(
                (
                    (connection["from"], connection["from_port"]),
                    (connection["to"], connection["to_port"]),
                )
            )
            signature = (*endpoints[0], *endpoints[1], connection["connection_type"])
            connection_signatures[signature] += 1
            if endpoints[0] == endpoints[1]:
                warn(
                    "topology",
                    f"Connection loops back to the same port: {endpoints[0][0]}.{endpoints[0][1]}",
                )
        duplicate_connections = sum(count - 1 for count in connection_signatures.values() if count > 1)
        if duplicate_connections:
            warn("topology", f"Architecture contains {duplicate_connections} duplicate connection(s)")

        components: list[set[str]] = []
        unvisited = set(element_ids)
        while unvisited:
            pending = [unvisited.pop()]
            component: set[str] = set()
            while pending:
                element_id = pending.pop()
                component.add(element_id)
                neighbors = adjacency[element_id] & unvisited
                unvisited.difference_update(neighbors)
                pending.extend(neighbors)
            components.append(component)
        if len(components) > 1:
            components.sort(key=len, reverse=True)
            disconnected = "; ".join(
                ", ".join(sorted(component)) for component in components[1:]
            )
            warn(
                "topology",
                f"Architecture has {len(components)} disconnected topology components; "
                f"elements outside the largest component: {disconnected}",
            )

        for element_id, ports in element_ports.items():
            if (
                element_types.get(element_id) in {"hub", "mux"}
                and "upstream" in ports
                and port_usage[(element_id, "upstream")] == 0
                and any(port_usage[(element_id, port_id)] for port_id in ports - {"upstream"})
            ):
                warn(
                    "topology",
                    f"{element_types[element_id].title()} {element_id} has connected downstream "
                    "ports but its upstream port is unconnected",
                )
            if element_types.get(element_id) in {"hub", "mux"} and "upstream" in ports:
                downstream_ports = ports - {"upstream"}
                if port_usage[(element_id, "upstream")] and downstream_ports and not any(
                    port_usage[(element_id, port_id)] for port_id in downstream_ports
                ):
                    warn(
                        "topology",
                        f"{element_types[element_id].title()} {element_id} has a connected upstream "
                        "port but no connected downstream ports",
                    )

            if element_types.get(element_id) in {
                "device",
                "eeprom",
                "endpoint",
                "sensor",
                "temperature_sensor",
            }:
                transit_ports = sorted(
                    port_id for port_id in ports if port_usage[(element_id, port_id)] > 1
                )
                if transit_ports:
                    warn(
                        "topology",
                        f"Terminal element {element_id} may be modeled as a transit device on ports: "
                        f"{', '.join(transit_ports)}",
                    )

        for element_id, ports in element_ports.items():
            if element_types.get(element_id) != "connector":
                continue
            mating_ports = {
                port_id
                for port_id in ports
                if "mating" in port_connection_types[(element_id, port_id)]
            }
            if not mating_ports:
                continue
            boundary_ports = {
                port_id
                for port_id in ports
                if port_connection_types[(element_id, port_id)] - {"mating"}
            }
            missing_mating = sorted(boundary_ports - mating_ports)
            if missing_mating:
                warn(
                    "topology",
                    f"Connector {element_id} has internally connected ports without mating "
                    f"coverage: {', '.join(missing_mating)}",
                )

    for name, check in checks.items():
        if error_counts[name]:
            check["detail"] = f"Validation failed; review {error_counts[name]} issue(s)"
        elif warning_counts[name]:
            check["detail"] = f"Review required; inspect {warning_counts[name]} warning(s)"
    return {
        "valid": not errors,
        "review_required": bool(warnings),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }


def build_repair_prompt(
    candidate: str,
    errors: Sequence[str],
) -> str:
    issues = "\n".join(f"- {error}" for error in errors)
    return f"""Return a minimal RFC 6902-style JSON patch that fixes only the structural validation errors in this YAML candidate.

Validator findings:
{issues}

Candidate:
```yaml
{candidate}
```

Return a JSON array only, without Markdown fences or explanation. Each item must contain op, path, and value for add or replace; remove is allowed only for an unsupported top-level key. Use JSON Pointer paths such as /elements/3/board. Never replace an entire board, element, port, connection, or top-level collection. Never remove boards, elements, ports, or connections. Make the fewest field-level edits needed to fix the listed errors.

Do not repair topology warnings, redesign connections, add source facts, or change labels. Preserve every existing board, element, port, and connection. This repair has no source PDF, so do not infer hardware facts."""


def _decode_json_pointer(path: str) -> list[str]:
    if not path.startswith("/"):
        raise YamlGenerationError(f"Repair patch path must be a JSON Pointer: {path}")
    return [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]


def _validate_patch_path(operation: str, parts: list[str]) -> None:
    protected_roots = {"boards", "elements", "connections"}
    if not parts or parts[0] == "version" and len(parts) > 1:
        raise YamlGenerationError("Repair patch targets an invalid architecture path")
    if parts[0] in protected_roots:
        if len(parts) == 1 or len(parts) == 2:
            raise YamlGenerationError("Repair patch cannot replace an architecture collection or item")
        if parts[0] == "elements" and len(parts) == 4 and parts[2] == "ports":
            raise YamlGenerationError("Repair patch cannot replace an existing port")
    if operation == "remove" and len(parts) != 1:
        raise YamlGenerationError("Repair patch cannot remove architecture content")


def _container_item(container: Any, part: str) -> Any:
    if isinstance(container, list):
        if not part.isdigit():
            raise YamlGenerationError(f"Repair patch has an invalid list index: {part}")
        index = int(part)
        if index >= len(container):
            raise YamlGenerationError(f"Repair patch list index is out of range: {part}")
        return container[index]
    if isinstance(container, dict) and part in container:
        return container[part]
    raise YamlGenerationError(f"Repair patch path does not exist: {part}")


def apply_repair_patch(document: dict[str, Any], content: str) -> dict[str, Any]:
    cleaned = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        operations = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise YamlGenerationError(f"Copilot returned an invalid repair patch: {exc}") from exc
    if not isinstance(operations, list) or not 1 <= len(operations) <= 64:
        raise YamlGenerationError("Repair patch must contain between 1 and 64 operations")

    repaired = copy.deepcopy(document)
    for patch in operations:
        if not isinstance(patch, dict):
            raise YamlGenerationError("Each repair patch operation must be an object")
        operation = patch.get("op")
        path = patch.get("path")
        if operation not in {"add", "replace", "remove"} or not isinstance(path, str):
            raise YamlGenerationError("Repair patch supports only add, replace, and remove")
        parts = _decode_json_pointer(path)
        _validate_patch_path(operation, parts)
        parent: Any = repaired
        for part in parts[:-1]:
            parent = _container_item(parent, part)
        key = parts[-1]
        if operation == "remove":
            if not isinstance(parent, dict) or key in ALLOWED_TOP_LEVEL_KEYS or key not in parent:
                raise YamlGenerationError("Repair patch can remove only an unsupported top-level key")
            del parent[key]
        elif isinstance(parent, list):
            if not key.isdigit() or int(key) >= len(parent):
                raise YamlGenerationError("Repair patch cannot append or replace architecture items")
            parent[int(key)] = patch.get("value")
        elif isinstance(parent, dict):
            if operation == "replace" and key not in parent:
                raise YamlGenerationError(f"Repair patch replace path does not exist: {path}")
            parent[key] = patch.get("value")
        else:
            raise YamlGenerationError(f"Repair patch parent is not a collection: {path}")
    return repaired


def _architecture_scope(document: dict[str, Any]) -> dict[str, Any]:
    boards = document.get("boards") if isinstance(document.get("boards"), list) else []
    elements = document.get("elements") if isinstance(document.get("elements"), list) else []
    connections = document.get("connections") if isinstance(document.get("connections"), list) else []
    ports = sum(
        len(element.get("ports", []))
        for element in elements
        if isinstance(element, dict) and isinstance(element.get("ports"), list)
    )
    labels = Counter(
        item["label"]
        for item in [*boards, *elements]
        if isinstance(item, dict) and isinstance(item.get("label"), str) and item["label"]
    )
    return {
        "boards": len(boards),
        "elements": len(elements),
        "ports": ports,
        "connections": len(connections),
        "labels": labels,
    }


def ensure_scope_preserved(before: dict[str, Any], after: dict[str, Any]) -> None:
    baseline = _architecture_scope(before)
    repaired = _architecture_scope(after)
    for key in ("boards", "elements", "ports", "connections"):
        if repaired[key] < baseline[key]:
            raise YamlGenerationError(f"Repair patch reduced architecture scope: {key}")
    if baseline["labels"] - repaired["labels"]:
        raise YamlGenerationError("Repair patch removed or changed source-supported labels")


async def generate_architecture_yaml(
    source_pdf: Path,
    reference_files: Sequence[Path],
    model: str | None = None,
    progress_callback: ProgressCallback | None = None,
    activity_callback: ActivityCallback | None = None,
    process_callback: ProcessCallback | None = None,
) -> tuple[str, dict[str, Any]]:
    selected_references = select_reference_files(reference_files)
    example_files = reviewed_example_files()
    with TemporaryDirectory(
        prefix="copilot-pdf-yaml-",
        dir=source_pdf.parent,
    ) as directory:
        workspace = Path(directory)
        workspace_source = workspace / source_pdf.name
        shutil.copy2(source_pdf, workspace_source)
        reference_directory = workspace / "references"
        reference_directory.mkdir()
        workspace_references: list[Path] = []
        for reference in selected_references:
            copied_reference = reference_directory / reference.name
            shutil.copy2(reference, copied_reference)
            workspace_references.append(copied_reference)
        reviewed_example_directory = reference_directory / "reviewed_example"
        reviewed_example_directory.mkdir()
        for reference in example_files:
            copied_reference = reviewed_example_directory / reference.name
            shutil.copy2(reference, copied_reference)
            workspace_references.append(copied_reference)

        return await _generate_architecture_yaml_in_workspace(
            workspace_source,
            workspace_references,
            workspace,
            model=model,
            progress_callback=progress_callback,
            activity_callback=activity_callback,
            process_callback=process_callback,
        )


async def _generate_architecture_yaml_in_workspace(
    source_pdf: Path,
    reference_files: Sequence[Path],
    workspace: Path,
    model: str | None = None,
    progress_callback: ProgressCallback | None = None,
    activity_callback: ActivityCallback | None = None,
    process_callback: ProcessCallback | None = None,
) -> tuple[str, dict[str, Any]]:
    async def report(stage: str, percent: int) -> None:
        if progress_callback is not None:
            await progress_callback(stage, percent)

    async def report_activity(activity: str) -> None:
        if activity_callback is not None:
            await activity_callback(activity)

    async def report_process(message: str) -> None:
        if process_callback is not None:
            await process_callback(message)

    await report("filtering", 10)
    filtered_pdf = source_pdf.with_name(f"{source_pdf.stem}_smbus_figures.pdf")
    try:
        selection = extract_architecture_pages(source_pdf, filtered_pdf)
    except ArchitectureFigureNotFoundError as exc:
        raise YamlGenerationError(str(exc)) from exc
    attachments = [filtered_pdf, *reference_files]
    prompt = build_generation_prompt(
        filtered_pdf.name,
        [path.relative_to(workspace).as_posix() for path in reference_files],
        selection,
        python_executable=sys.executable,
    )
    await report("generating", 25)
    await report_activity("context_ready")
    generation_percent = 25
    last_activity_at = 0.0
    process_buffer = ""
    last_process_message = ""

    def clean_process_message(message: str) -> str:
        cleaned = re.sub(r"[`#*_>]", "", message)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:\n\t")
        return cleaned[:177] + "..." if len(cleaned) > 180 else cleaned

    def report_generation_activity(activity: str) -> None:
        nonlocal generation_percent, last_activity_at
        now = time.monotonic()
        if now - last_activity_at < 5 or generation_percent >= 55:
            return
        last_activity_at = now
        generation_percent += 1
        asyncio.get_running_loop().create_task(report("generating", generation_percent))
        asyncio.get_running_loop().create_task(report_activity(activity))

    def report_process_activity(delta: str) -> None:
        nonlocal process_buffer, last_process_message
        report_generation_activity("analyzing")
        process_buffer += delta
        while True:
            boundary = re.search(r"(?:[.!?。！？](?:\s|$)|\n)", process_buffer)
            if boundary is None and len(process_buffer) < 180:
                break
            end = boundary.end() if boundary is not None else 180
            message = clean_process_message(process_buffer[:end])
            process_buffer = process_buffer[end:]
            if len(message) < 12 or message == last_process_message:
                continue
            last_process_message = message
            asyncio.get_running_loop().create_task(report_process(message))

    def report_output_activity(_: str) -> None:
        report_generation_activity("writing_yaml")

    def report_tool_activity(_: str) -> None:
        report_generation_activity("inspecting_inputs")

    content = await ask_copilot(
        prompt,
        model=model or os.getenv("PDF_YAML_MODEL", "gpt-5.4-mini"),
        files=attachments,
        workspace=workspace,
        workspace_guidance=PDF_WORKSPACE_GUIDANCE,
        timeout=timeout_from_env(
            "PDF_YAML_GENERATION_TIMEOUT_SECONDS",
            DEFAULT_GENERATION_TIMEOUT_SECONDS,
        ),
        on_delta=report_output_activity,
        on_process_delta=report_process_activity,
        on_activity=report_tool_activity,
    )
    remaining_process = clean_process_message(process_buffer)
    if len(remaining_process) >= 12 and remaining_process != last_process_message:
        await report_process(remaining_process)
    await report_activity("response_received")
    await report("validating", 65)
    candidate = strip_yaml_fence(content)
    validation = validate_architecture_yaml(candidate)
    if validation["valid"]:
        await report("completed", 100)
        return candidate, validation

    try:
        original_document = yaml.safe_load(candidate)
    except yaml.YAMLError as exc:
        raise YamlGenerationError(
            "Copilot returned invalid YAML syntax that cannot be safely patched; regenerate the YAML"
        ) from exc
    if not isinstance(original_document, dict):
        raise YamlGenerationError(
            "Copilot returned a non-mapping YAML document that cannot be safely patched"
        )

    await report("repairing", 72)
    await report_activity("repairing_yaml")
    patch_content = await ask_copilot(
        build_repair_prompt(candidate, validation["errors"]),
        model=model or os.getenv("PDF_YAML_MODEL", "gpt-5.4-mini"),
        files=[],
        workspace=workspace,
        workspace_guidance=PDF_WORKSPACE_GUIDANCE,
        timeout=timeout_from_env(
            "PDF_YAML_REPAIR_TIMEOUT_SECONDS",
            DEFAULT_REPAIR_TIMEOUT_SECONDS,
        ),
    )
    await report("revalidating", 95)
    repaired_document = apply_repair_patch(original_document, patch_content)
    ensure_scope_preserved(original_document, repaired_document)
    candidate = yaml.safe_dump(repaired_document, sort_keys=False, allow_unicode=True).strip()
    validation = validate_architecture_yaml(candidate)
    if not validation["valid"]:
        raise YamlGenerationError(
            "Copilot returned non-compliant YAML after one repair attempt: "
            + "; ".join(validation["errors"][:5])
        )
    await report("completed", 100)
    return candidate, validation