import json
import re
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import pymupdf
import yaml

from pdf_to_yaml_agent.ollama_client import OllamaClient, OllamaError
from pdf_to_yaml_agent.config import (
    GENERATION_TIMEOUT_SECONDS,
    OLLAMA_CONTEXT_WINDOW,
    TEXT_MAX_OUTPUT_TOKENS,
    VISION_MAX_OUTPUT_TOKENS,
    text_model,
    vision_model,
)
from pdf_to_yaml_agent.pdf_filter import ArchitectureSelection


ProgressCallback = Callable[[str, int], Awaitable[None]]
MessageCallback = Callable[[str], Awaitable[None]]
ALLOWED_TOP_LEVEL_KEYS = {"version", "boards", "elements", "connections"}


def render_analysis_images(
    filtered_pdf: Path,
    selection: ArchitectureSelection,
    analysis_directory: Path,
) -> tuple[str, list[Path]]:
    page_text, manifest = render_analysis_inputs(
        filtered_pdf, selection, analysis_directory
    )
    return page_text, [Path(item["path"]) for item in manifest]


def render_analysis_inputs(
    filtered_pdf: Path,
    selection: ArchitectureSelection,
    analysis_directory: Path,
) -> tuple[str, list[dict]]:
    analysis_directory.mkdir(parents=True, exist_ok=True)
    target_index = next(
        (
            index
            for index, figure in enumerate(selection.figures)
            if figure.page_number == selection.target.page_number
        ),
        len(selection.figures) - 1,
    )
    with pymupdf.open(filtered_pdf) as document:
        page = document[target_index]
        page_text = page.get_text("text")
        overview = analysis_directory / "target_overview.png"
        page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).save(overview)

        manifest: list[dict] = [
            {
                "name": overview.name,
                "path": str(overview),
                "kind": "overview",
                "bbox": [0, 0, page.rect.width, page.rect.height],
                "text": page_text,
            }
        ]
        columns = rows = 3
        overlap = 0.08
        width = page.rect.width / columns
        height = page.rect.height / rows
        for row in range(rows):
            for column in range(columns):
                x0 = max(0, column * width - width * overlap)
                y0 = max(0, row * height - height * overlap)
                x1 = min(page.rect.width, (column + 1) * width + width * overlap)
                y1 = min(page.rect.height, (row + 1) * height + height * overlap)
                crop = analysis_directory / f"target_r{row + 1}_c{column + 1}.png"
                page.get_pixmap(
                    matrix=pymupdf.Matrix(4, 4),
                    clip=pymupdf.Rect(x0, y0, x1, y1),
                    alpha=False,
                ).save(crop)
                clip = pymupdf.Rect(x0, y0, x1, y1)
                manifest.append(
                    {
                        "name": crop.name,
                        "path": str(crop),
                        "kind": "crop",
                        "row": row + 1,
                        "column": column + 1,
                        "bbox": [x0, y0, x1, y1],
                        "text": page.get_text("text", clip=clip),
                    }
                )
    (analysis_directory / "crop_manifest.json").write_text(
        json.dumps(
            [{key: value for key, value in item.items() if key != "path"} for item in manifest],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return page_text, manifest


def build_vision_prompt(
    selection: ArchitectureSelection,
    image_name: str,
    image_index: int,
    image_count: int,
    source_text: str = "",
    source_region: Sequence[float] | None = None,
) -> str:
    region = list(source_region) if source_region is not None else []
    return f"""Inspect this image from {selection.target.caption}. It is image {image_index} of {image_count}, named {image_name}, with PDF coordinates {region}.

The PDF text layer intersecting this exact image region is provided below. Use it to resolve tiny labels, but use the image lines and boundaries to determine topology:
--- region text ---
{source_text[:20_000]}
--- end region text ---

Extract only facts visibly supported by this image. Return one JSON object with these keys:
- boards: array of objects with label and evidence
- elements: array of objects with label, board_label, type, part, address, ports, evidence
- connections: array of objects with from_element, from_port, to_element, to_port, connection_type, protocol, signal, evidence
- boundaries: array describing connector-only, reserved, optional, repeated-slot, internal-only, or off-page paths
- visible_labels: array of important labels exactly as printed

For evidence use the image name. Preserve exact part numbers, hexadecimal addresses, connector names, channel numbers, and signal names. Follow every visible line through hubs, muxes, buffers, translators, connector arrays, cables, and endpoint devices. A declared mux or hub output is not a connection unless its visible destination is identified. Treat symbols defined by the figure legend as element annotations, not ports, signal names, or evidence of a connection. A connection requires a visible line or path between endpoints. Do not infer facts hidden outside this image. Use empty arrays for categories not visible. Return JSON only."""


def _reference_context(reference_files: Sequence[Path], max_characters: int = 30_000) -> str:
    sections: list[str] = []
    remaining = max_characters
    for path in reference_files:
        suffix = path.suffix.lower()
        if suffix not in {".md", ".txt", ".yaml", ".yml", ".pdf"}:
            continue
        if suffix in {".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            try:
                example = yaml.safe_load(text)
            except yaml.YAMLError:
                continue
            if not isinstance(example, dict):
                continue
            shape: dict[str, list[str]] = {}
            for section in ("boards", "elements", "connections"):
                items = example.get(section)
                fields = {
                    key
                    for item in (items if isinstance(items, list) else [])
                    for key in (item.keys() if isinstance(item, dict) else ())
                }
                shape[section] = sorted(fields)
            element_types = sorted(
                {
                    str(item.get("type"))
                    for item in example.get("elements", [])
                    if isinstance(item, dict) and item.get("type")
                }
            )
            connection_types = sorted(
                {
                    str(item.get("connection_type"))
                    for item in example.get("connections", [])
                    if isinstance(item, dict) and item.get("connection_type")
                }
            )
            protocols = sorted(
                {
                    str(item.get("protocol"))
                    for item in example.get("connections", [])
                    if isinstance(item, dict) and item.get("protocol")
                }
            )
            profile = {
                "top_level_order": [
                    key
                    for key in example
                    if key in {"version", "boards", "elements", "connections"}
                ],
                **shape,
                "id_style": "lowercase_snake_case",
                "element_types": element_types[:64],
                "connection_types": connection_types,
                "protocols": protocols[:32],
                "address_style": "quoted_string",
            }
            excerpt = json.dumps(profile, ensure_ascii=False)
            sections.append(
                f"\n--- {path.name} representation profile only; hardware values omitted ---\n{excerpt}"
            )
        elif suffix == ".pdf":
            try:
                with pymupdf.open(path) as document:
                    excerpt = "\n".join(page.get_text("text") for page in document)[:remaining]
            except (OSError, RuntimeError):
                continue
            sections.append(
                f"\n--- {path.name} normative text; representation rules only ---\n{excerpt}"
            )
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if suffix == ".md":
                text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
            excerpt = text[:remaining]
            sections.append(
                f"\n--- {path.name} normative text; representation rules only ---\n{excerpt}"
            )
        remaining -= len(excerpt)
        if remaining <= 0:
            break
    return "".join(sections)


def build_structure_prompt(
    selection: ArchitectureSelection,
    page_text: str,
    inventory: list[dict | list],
    references: str,
) -> str:
    return f"""Merge the visual extraction fragments into the complete board, element, and port inventory for {selection.target.caption}.

The target figure is the only authority for hardware facts. Reference YAML values are never source facts. Deduplicate overlapping crop observations, but preserve every visibly distinct board, controller, hub, mux, buffer, translator, connector, cable endpoint, repeated slot, address, and named channel. Never combine devices merely because they have the same part number or share a bus.

Return JSON only with exactly these keys:
{{"boards": [], "elements": []}}

Requirements:
- Board and element IDs use lowercase snake_case. Element IDs are globally unique; port IDs are unique within an element.
- Each board has id and label. Each element has id, board, type, and a non-empty ports array.
- Create separate elements for distinct addresses, numbered instances, repeated slots, muxes, connector endpoints, and distribution layers.
- Ports must cover every source-supported connection endpoint present in the visual inventory.
- Preserve source-supported part and quoted hexadecimal address values when visible.
- Do not expand a referenced detail diagram that is not visible in the authoritative target.
- Do not add evidence, confidence, notes, metadata, or custom keys.

PDF text layer:
{page_text[:40_000]}

Visual inventory fragments:
{json.dumps(inventory, ensure_ascii=False)}

Normative authoring references:
{references}"""


def normalize_structure(result: dict | list) -> dict:
    if not isinstance(result, dict) or set(result) != {"boards", "elements"}:
        raise OllamaError("Text model returned an invalid board/element structure")
    if not isinstance(result["boards"], list) or not isinstance(result["elements"], list):
        raise OllamaError("Text model returned non-list boards or elements")
    return {"boards": result["boards"], "elements": result["elements"]}


def build_fragment_structure_prompt(
    fragment: dict | list,
    fragment_name: str,
    references: str = "",
) -> str:
    reference_guidance = (
        "\n\nNormative representation guidance:\n"
        "Use this only for schema, field selection, ID style, type vocabulary, and naming "
        "conventions. Never copy boards, devices, part numbers, addresses, labels, ports, or "
        "connections from a reference unless the raw region facts independently show them.\n"
        f"{references}"
        if references
        else ""
    )
    return f"""Clean this one-region visual extraction from {fragment_name} into source-supported board and physical-device facts.

Return JSON only as {{"boards": [], "elements": [], "connections": []}}.

Rules:
- A board is a visible physical board, module, riser, backplane, adapter, or card boundary.
- An element is a physical controller, PLD/CPLD, hub, mux, buffer, translator, connector, cable endpoint, EEPROM/FRU, sensor, regulator, monitor, slot, drive, or other target device.
- Do not turn signal names, bus names, protocol names, voltage rails, frequencies, addresses by themselves, figure titles, evidence filenames, or notes into elements.
- Preserve every distinct visible instance. Devices with different addresses, channel numbers, slot numbers, or board boundaries remain separate.
- Each board requires lowercase snake_case id and label.
- Each element requires lowercase snake_case id, board, label, type, and ports as an array of objects with stable ids. Preserve source spelling and case for port ids so connection references resolve exactly. Include part and quoted hexadecimal address only when supported.
- Create an upstream/downstream or bus port when a physical device has a visible connection but the extracted port list is empty.
- Every element.board must match a returned board id. Do not infer facts outside this region.
- Every connection endpoint must use the exact id of a returned physical element. A board boundary, bus label, signal label, voltage rail, note, or off-page arrow is not an endpoint.
- Put a visible bus or net name in signal and its protocol in protocol. Use connection_type internal_net, mating, or cable.
- internal_net is allowed only when both elements are on the same board. Crossing a physical board boundary requires a visible connector and mating or cable.
- Do not chain EEPROMs, sensors, FRUs, regulators, or other terminal devices together to represent a shared bus. Connect each visible branch to its actual controller, hub, mux, or connector.
- Preserve visible hubs, muxes, buffers, translators, connectors, and cable endpoints as separate hops; never bypass them.
- Omit a raw connection when either physical endpoint is not visible in this region. Do not invent its missing endpoint.

Raw region facts:
{json.dumps(fragment, ensure_ascii=False)}{reference_guidance}"""


def normalize_fragment(result: dict | list) -> dict:
    if not isinstance(result, dict) or set(result) != {
        "boards",
        "elements",
        "connections",
    }:
        raise OllamaError("Text model returned an invalid region structure")
    if not all(isinstance(result[key], list) for key in result):
        raise OllamaError("Text model returned non-list region facts")
    return {
        "boards": result["boards"],
        "elements": result["elements"],
        "connections": result["connections"],
    }


def invalid_fragment_connections(fragment: dict) -> list[dict]:
    element_ids = {
        item.get("id")
        for item in fragment.get("elements", [])
        if isinstance(item, dict) and item.get("id")
    }
    return [
        connection
        for connection in fragment.get("connections", [])
        if isinstance(connection, dict)
        and (
            (connection.get("from") or connection.get("from_element")) not in element_ids
            or (connection.get("to") or connection.get("to_element")) not in element_ids
        )
    ]


def build_fragment_repair_prompt(fragment: dict, invalid: Sequence[dict]) -> str:
    return f"""Repair only the invalid connection endpoints in this one-region architecture JSON.

Return JSON only with exactly boards, elements, and connections arrays.

Requirements:
- Every connection uses from_element, from_port, to_element, to_port, connection_type, protocol, and signal.
- from_element and to_element must exactly equal an element id returned in elements.
- When an invalid endpoint is a visible physical connector, slot, cable endpoint, or device, add that distinct physical element with its visible board and ports.
- When an invalid endpoint is only a bus, signal, rail, board boundary, off-page arrow, or note, omit that connection instead of inventing a device.
- Keep every already valid board, element, port, and connection unchanged.
- Do not add facts absent from this region.

Invalid connections:
{json.dumps(list(invalid), ensure_ascii=False)}

Current region JSON:
{json.dumps(fragment, ensure_ascii=False)}"""


def materialize_connector_endpoints(fragment: dict) -> dict:
    elements = fragment.get("elements", [])
    known_ids = {
        element.get("id")
        for element in elements
        if isinstance(element, dict) and element.get("id")
    }
    board_ids = [
        board.get("id")
        for board in fragment.get("boards", [])
        if isinstance(board, dict) and board.get("id")
    ]
    connector_pattern = re.compile(
        r"(?:^|_)(?:connector|conn|slot|socket|header|receptacle|plug)(?:_|$)"
    )
    for connection in fragment.get("connections", []):
        if not isinstance(connection, dict):
            continue
        for endpoint_key, port_key, peer_key in (
            ("from_element", "from_port", "to_element"),
            ("to_element", "to_port", "from_element"),
        ):
            endpoint = connection.get(endpoint_key) or connection.get(
                endpoint_key.removesuffix("_element")
            )
            endpoint_id = _slug(endpoint, "")
            if (
                not endpoint_id
                or endpoint_id in known_ids
                or connector_pattern.search(endpoint_id) is None
            ):
                continue
            peer_id = connection.get(peer_key) or connection.get(
                peer_key.removesuffix("_element")
            )
            peer = next(
                (
                    element
                    for element in elements
                    if isinstance(element, dict) and element.get("id") == peer_id
                ),
                None,
            )
            board_id = (
                peer.get("board")
                if isinstance(peer, dict) and peer.get("board")
                else (board_ids[0] if board_ids else "unassigned")
            )
            elements.append(
                {
                    "id": endpoint_id,
                    "board": board_id,
                    "label": str(endpoint).replace("_", " "),
                    "type": "connector",
                    "ports": [{"id": str(connection.get(port_key) or "bus")}],
                }
            )
            known_ids.add(endpoint_id)
    return fragment


def build_topology_completion_prompt(fragment: dict, fragment_name: str) -> str:
    elements = [
        {
            key: element.get(key)
            for key in ("id", "label", "type", "part", "address", "ports")
            if element.get(key) not in (None, "")
        }
        for element in fragment.get("elements", [])
        if isinstance(element, dict)
    ]
    return f"""Trace the visible topology lines in {fragment_name} using the canonical element list below.

Return JSON only as {{"connections": []}}. Each connection requires from_element, from_port, to_element, to_port, connection_type, protocol, and signal.

Rules:
- from_element and to_element must exactly equal ids in the canonical list.
- Include every visible line whose two physical endpoints are in the list.
- Follow each line through every visible hub, mux, buffer, translator, connector, and cable endpoint; preserve these as separate hops.
- A board boundary, bus/net label, signal label, voltage rail, note, or off-page arrow is not an endpoint.
- Do not connect elements based only on proximity or shared protocol.
- Treat symbols defined by the figure legend as element annotations, not ports, signal names, or evidence of a connection. A connection requires a visible line or path between endpoints.
- Use internal_net, mating, or cable for connection_type.
- Use internal_net only for elements on the same board. A cross-board connection requires a visible connector boundary and mating or cable.
- Do not connect terminal devices to each other merely because they share a bus label; preserve the visible controller, hub, mux, or connector as the branch source.
- Keep distinct ports and repeated connector instances separate.

Canonical elements:
{json.dumps(elements, ensure_ascii=False)}

Already extracted connections; include them when visibly correct and add omitted visible lines:
{json.dumps(fragment.get("connections", []), ensure_ascii=False)}"""


def merge_fragment_connections(fragment: dict, result: dict | list) -> dict:
    if not isinstance(result, dict) or set(result) != {"connections"}:
        raise OllamaError("Vision model returned an invalid topology completion")
    additions = result["connections"]
    if not isinstance(additions, list):
        raise OllamaError("Vision model returned non-list topology connections")
    connections = fragment.setdefault("connections", [])
    signatures = {
        json.dumps(connection, sort_keys=True, ensure_ascii=False)
        for connection in connections
        if isinstance(connection, dict)
    }
    for connection in additions:
        if not isinstance(connection, dict):
            continue
        signature = json.dumps(connection, sort_keys=True, ensure_ascii=False)
        if signature not in signatures:
            connections.append(connection)
            signatures.add(signature)
    return fragment


def isolated_physical_element_ids(fragment: dict) -> list[str]:
    connected_ids = {
        endpoint
        for connection in fragment.get("connections", [])
        if isinstance(connection, dict)
        for endpoint in (
            connection.get("from") or connection.get("from_element"),
            connection.get("to") or connection.get("to_element"),
        )
        if endpoint
    }
    return [
        element["id"]
        for element in fragment.get("elements", [])
        if isinstance(element, dict)
        and element.get("id")
        and not _is_nonphysical_element(element)
        and element["id"] not in connected_ids
    ]


def _slug(value: object, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")
    return slug or fallback


def _is_nonphysical_element(element: dict) -> bool:
    element_type = _slug(element.get("type"))
    if element_type in {"bus", "signal", "smbus", "voltage"}:
        return True
    return (
        not element.get("part")
        and not element.get("address")
        and element_type.endswith(("_bus", "_channel", "_interface", "_port"))
    )


def merge_structures(structures: Sequence[dict]) -> dict:
    boards_by_id: dict[str, dict] = {}
    element_records: list[tuple[tuple[str, str, str, str], dict]] = []
    for structure in structures:
        board_aliases: dict[str, str] = {}
        for board in structure.get("boards", []):
            if not isinstance(board, dict):
                continue
            label = str(board.get("label") or board.get("id") or "").strip()
            if not label:
                continue
            board_id = _slug(board.get("id") or label, "board")
            board_aliases[str(board.get("id") or board_id)] = board_id
            boards_by_id.setdefault(board_id, {"id": board_id, "label": label})
        for element in structure.get("elements", []):
            if not isinstance(element, dict):
                continue
            label = str(element.get("label") or element.get("id") or "").strip()
            if not label:
                continue
            raw_board = str(element.get("board") or "unassigned")
            board_id = board_aliases.get(raw_board, _slug(raw_board, "unassigned"))
            boards_by_id.setdefault(
                board_id,
                {"id": board_id, "label": raw_board if raw_board != "unassigned" else "Unassigned"},
            )
            part = str(element.get("part") or "").strip()
            address = str(element.get("address") or "").strip()
            identity = (board_id, _slug(label), _slug(part, ""), _slug(address, ""))
            normalized = {
                "id": _slug(element.get("id") or label, "element"),
                "board": board_id,
                "label": label,
                "type": _slug(element.get("type"), "device"),
                "ports": [],
            }
            for key in ("mechanical", "port_display_order"):
                if key in element:
                    normalized[key] = element[key]
            if part:
                normalized["part"] = part
            if address:
                normalized["address"] = address
            ports_by_id: dict[str, dict] = {}
            ports = element.get("ports")
            for port in ports if isinstance(ports, list) else []:
                if not isinstance(port, dict):
                    continue
                raw_port = port.get("id")
                port_id = str(raw_port) if raw_port not in (None, "") else "bus"
                normalized_port = dict(port)
                normalized_port["id"] = port_id
                current_port = ports_by_id.get(port_id)
                if current_port is None:
                    ports_by_id[port_id] = normalized_port
                else:
                    current_port.update(
                        {key: value for key, value in normalized_port.items() if key != "id"}
                    )
            normalized["ports"] = list(ports_by_id.values())
            if not normalized["ports"]:
                normalized["ports"] = [{"id": "bus"}]
            element_records.append((identity, normalized))

    merged_by_identity: dict[tuple[str, str, str, str], dict] = {}
    for identity, element in element_records:
        current = merged_by_identity.get(identity)
        if current is None:
            merged_by_identity[identity] = element
            continue
        existing_ports = {port["id"] for port in current["ports"]}
        current["ports"].extend(
            port for port in element["ports"] if port["id"] not in existing_ports
        )

    used_ids: set[str] = set()
    elements: list[dict] = []
    for element in merged_by_identity.values():
        base_id = element["id"]
        element_id = base_id
        suffix = 2
        while element_id in used_ids:
            element_id = f"{base_id}_{suffix}"
            suffix += 1
        element["id"] = element_id
        used_ids.add(element_id)
        elements.append(element)
    return {"boards": list(boards_by_id.values()), "elements": elements}


def build_connections_prompt(
    selection: ArchitectureSelection,
    inventory: list[dict | list],
    structure: dict,
) -> str:
    return f"""Compile every source-supported physical or logical hop in {selection.target.caption} into connections using only the declared element and port IDs below.

Return JSON only as {{"connections": []}}. Every connection requires from, from_port, to, to_port, and connection_type. connection_type must be internal_net, mating, or cable. Include protocol, signal, voltage_domain, speed_hz, or medium only when explicitly supported.

Rules:
- Preserve distribution layers. Never bypass a visible hub, mux, buffer, translator, connector, cable endpoint, or power-distribution connector.
- Do not create both a direct path and an alternate mux/hub path for the same physical route.
- Represent every visible branch and repeated destination separately.
- Do not invent destinations for reserved, optional, connector-only, internal-only, or off-page paths.
- Every endpoint must exactly resolve to the supplied structure.

Visual inventory fragments:
{json.dumps(inventory, ensure_ascii=False)}

Declared structure:
{json.dumps(structure, ensure_ascii=False)}"""


def compile_architecture(structure: dict, result: dict | list) -> dict:
    if not isinstance(result, dict) or set(result) != {"connections"}:
        raise OllamaError("Text model returned an invalid connection structure")
    if not isinstance(result["connections"], list):
        raise OllamaError("Text model returned non-list connections")
    return {
        "version": 1,
        "boards": structure["boards"],
        "elements": structure["elements"],
        "connections": result["connections"],
    }


def collapse_nonphysical_elements(architecture: dict) -> dict:
    elements_by_id = {
        element["id"]: element
        for element in architecture["elements"]
        if isinstance(element, dict) and element.get("id")
    }
    nonphysical_ids = {
        element_id
        for element_id, element in elements_by_id.items()
        if _is_nonphysical_element(element)
    }
    if not nonphysical_ids:
        return architecture

    connections = [
        connection
        for connection in architecture["connections"]
        if isinstance(connection, dict)
    ]
    adjacency: dict[str, set[str]] = {element_id: set() for element_id in nonphysical_ids}
    for connection in connections:
        source = connection.get("from")
        destination = connection.get("to")
        if source in nonphysical_ids and destination in nonphysical_ids:
            adjacency[source].add(destination)
            adjacency[destination].add(source)

    additions: list[dict] = []
    visited: set[str] = set()
    for start in nonphysical_ids:
        if start in visited:
            continue
        component: set[str] = set()
        pending = [start]
        while pending:
            current = pending.pop()
            if current in component:
                continue
            component.add(current)
            visited.add(current)
            pending.extend(adjacency[current] - component)

        endpoints: list[tuple[str, str]] = []
        signals: list[str] = []
        protocols: list[str] = []
        for connection in connections:
            source = connection.get("from")
            destination = connection.get("to")
            if source in component and destination not in nonphysical_ids:
                endpoints.append((destination, connection.get("to_port") or "bus"))
            elif destination in component and source not in nonphysical_ids:
                endpoints.append((source, connection.get("from_port") or "bus"))
            else:
                continue
            if connection.get("signal"):
                signals.append(str(connection["signal"]))
            if connection.get("protocol"):
                protocols.append(str(connection["protocol"]))
        endpoints = list(dict.fromkeys(endpoints))
        if len(endpoints) < 2:
            continue
        anchor_id, anchor_port = endpoints[0]
        signal = signals[0] if signals else elements_by_id[start].get("label", start)
        for destination_id, destination_port in endpoints[1:]:
            connection = {
                "from": anchor_id,
                "from_port": anchor_port,
                "to": destination_id,
                "to_port": destination_port,
                "connection_type": "internal_net",
                "signal": signal,
            }
            if protocols:
                connection["protocol"] = protocols[0]
            additions.append(connection)

    retained = [
        connection
        for connection in connections
        if connection.get("from") not in nonphysical_ids
        and connection.get("to") not in nonphysical_ids
    ]
    signatures: set[tuple[str, str, str, str, str]] = set()
    deduplicated: list[dict] = []
    for connection in retained + additions:
        signature = (
            str(connection.get("from")),
            str(connection.get("from_port")),
            str(connection.get("to")),
            str(connection.get("to_port")),
            str(connection.get("connection_type")),
        )
        reverse = (signature[2], signature[3], signature[0], signature[1], signature[4])
        if signature not in signatures and reverse not in signatures:
            signatures.add(signature)
            deduplicated.append(connection)
    architecture["elements"] = [
        element
        for element in architecture["elements"]
        if element.get("id") not in nonphysical_ids
    ]
    architecture["connections"] = deduplicated
    return architecture


def compile_inventory_connections(
    structure: dict,
    inventory: Sequence[dict | list],
    fragment_structures: Sequence[dict | None] | None = None,
) -> tuple[list[dict], list[dict]]:
    elements = structure["elements"]
    aliases: dict[str, list[dict]] = {}
    for element in elements:
        for value in (element.get("id"), element.get("label"), element.get("part")):
            alias = re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())
            if len(alias) >= 3:
                matches = aliases.setdefault(alias, [])
                if element not in matches:
                    matches.append(element)

    def resolve_from(value: object, candidates_by_alias: dict[str, list[dict]]) -> dict | None:
        target = re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())
        if len(target) < 3:
            return None
        exact = candidates_by_alias.get(target, [])
        exact_ids = [
            element
            for element in exact
            if re.sub(
                r"[^a-z0-9]+", "", str(element.get("id") or "").casefold()
            )
            == target
        ]
        if len(exact_ids) == 1:
            return exact_ids[0]
        if len(exact) == 1:
            return exact[0]
        candidates = {
            element["id"]: element
            for alias, matches in candidates_by_alias.items()
            if len(alias) >= 4 and (target in alias or alias in target)
            for element in matches
        }
        return next(iter(candidates.values())) if len(candidates) == 1 else None

    def global_element(local: dict) -> dict | None:
        matches = [
            element
            for element in elements
            if element.get("board") == _slug(local.get("board"), "unassigned")
            and _slug(element.get("label")) == _slug(local.get("label") or local.get("id"))
            and _slug(element.get("part"), "") == _slug(local.get("part"), "")
            and _slug(element.get("address"), "") == _slug(local.get("address"), "")
        ]
        return matches[0] if len(matches) == 1 else None

    def ensure_port(element: dict, raw_port: object) -> str:
        port_id = str(raw_port) if raw_port not in (None, "") else "bus"
        ports = element.setdefault("ports", [])
        if not any(
            isinstance(port, dict) and port.get("id") == port_id for port in ports
        ):
            ports.append({"id": port_id})
        return port_id

    compiled: list[dict] = []
    unresolved: list[dict] = []
    signatures: set[tuple[str, str, str, str, str]] = set()
    type_map = {
        "direct": "internal_net",
        "internal": "internal_net",
        "internal_net": "internal_net",
        "mating": "mating",
        "cable": "cable",
        "cabled": "cable",
    }
    for fragment_index, fragment in enumerate(inventory):
        if not isinstance(fragment, dict):
            continue
        local_aliases: dict[str, list[dict]] | None = None
        if fragment_structures is not None and fragment_index < len(fragment_structures):
            local_structure = fragment_structures[fragment_index]
            if isinstance(local_structure, dict):
                local_aliases = {}
                for element in local_structure.get("elements", []):
                    if not isinstance(element, dict):
                        continue
                    for value in (element.get("id"), element.get("label"), element.get("part")):
                        alias = re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())
                        if len(alias) >= 3:
                            matches = local_aliases.setdefault(alias, [])
                            if element not in matches:
                                matches.append(element)
        for raw in fragment.get("connections", []):
            if not isinstance(raw, dict):
                continue
            source_value = raw.get("from_element") or raw.get("from")
            destination_value = raw.get("to_element") or raw.get("to")
            if local_aliases is None:
                source = resolve_from(source_value, aliases)
                destination = resolve_from(destination_value, aliases)
            else:
                local_source = resolve_from(source_value, local_aliases)
                local_destination = resolve_from(destination_value, local_aliases)
                source = global_element(local_source) if local_source is not None else None
                destination = (
                    global_element(local_destination)
                    if local_destination is not None
                    else None
                )
            if source is None or destination is None or source["id"] == destination["id"]:
                unresolved.append(raw)
                continue
            source_port = ensure_port(source, raw.get("from_port"))
            destination_port = ensure_port(destination, raw.get("to_port"))
            connection_type = type_map.get(
                str(raw.get("connection_type") or "").casefold(), "internal_net"
            )
            signature = (
                source["id"], source_port, destination["id"], destination_port, connection_type
            )
            reverse = (
                destination["id"], destination_port, source["id"], source_port, connection_type
            )
            if signature in signatures or reverse in signatures:
                continue
            signatures.add(signature)
            connection = {
                "from": source["id"],
                "from_port": source_port,
                "to": destination["id"],
                "to_port": destination_port,
                "connection_type": connection_type,
            }
            for key in (
                "protocol",
                "signal",
                "voltage_domain",
                "speed_hz",
                "medium",
                "length_mm",
                "from_role",
                "to_role",
            ):
                value = raw.get(key)
                if value not in (None, ""):
                    connection[key] = str(value).casefold() if key == "protocol" else value
            compiled.append(connection)
    return compiled, unresolved


def normalize_architecture(result: dict | list) -> dict:
    if not isinstance(result, dict):
        raise OllamaError("Text model returned a non-object architecture")
    extra = set(result) - ALLOWED_TOP_LEVEL_KEYS
    if extra:
        raise OllamaError(
            "Text model returned unsupported architecture keys: " + ", ".join(sorted(extra))
        )
    document = {
        "version": result.get("version"),
        "boards": result.get("boards"),
        "elements": result.get("elements"),
        "connections": result.get("connections"),
    }
    if document["version"] != 1 or not all(
        isinstance(document[key], list) for key in ("boards", "elements", "connections")
    ):
        raise OllamaError("Text model returned an invalid architecture shape")
    return document


def write_audit(
    analysis_directory: Path,
    inventory: list[dict | list],
    architecture: dict,
    validation: dict,
) -> dict:
    candidate_terms = {
        re.sub(r"[^a-z0-9]+", "", str(value).casefold())
        for section in ("boards", "elements")
        for item in architecture.get(section, [])
        if isinstance(item, dict)
        for value in (item.get("id"), item.get("label"), item.get("part"))
        if value
    }
    missing_labels: set[str] = set()
    for fragment in inventory:
        if not isinstance(fragment, dict):
            continue
        for item in fragment.get("elements", []):
            if not isinstance(item, dict):
                continue
            if _is_nonphysical_element(item):
                continue
            label = item.get("label") or item.get("part")
            normalized = re.sub(r"[^a-z0-9]+", "", str(label).casefold())
            if len(normalized) >= 4 and not any(
                normalized in candidate or candidate in normalized
                for candidate in candidate_terms
                if candidate
            ):
                missing_labels.add(str(label))
    connected_ids = {
        endpoint
        for connection in architecture.get("connections", [])
        if isinstance(connection, dict)
        for endpoint in (connection.get("from"), connection.get("to"))
        if endpoint
    }
    isolated_elements = [
        element.get("id")
        for element in architecture.get("elements", [])
        if isinstance(element, dict) and element.get("id") not in connected_ids
    ]
    audit = {
        "review_required": bool(
            isolated_elements
            or missing_labels
            or validation.get("errors")
            or validation.get("warnings")
        ),
        "missing_visual_elements": sorted(missing_labels),
        "isolated_elements": isolated_elements,
        "compiled_connection_count": len(architecture.get("connections", [])),
        "validation_errors": validation.get("errors", []),
        "topology_warnings": validation.get("warnings", []),
    }
    (analysis_directory / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return audit


async def run_ollama_conversion(
    filtered_pdf: Path,
    reference_files: Sequence[Path],
    selection: ArchitectureSelection,
    workspace: Path,
    progress_callback: ProgressCallback | None = None,
    activity_callback: MessageCallback | None = None,
    process_callback: MessageCallback | None = None,
) -> str:
    async def progress(percent: int) -> None:
        if progress_callback is not None:
            await progress_callback("generating", percent)

    async def activity(message: str) -> None:
        if activity_callback is not None:
            await activity_callback(message)

    selected_text_model = text_model()
    selected_vision_model = vision_model()
    client = OllamaClient(
        timeout=GENERATION_TIMEOUT_SECONDS,
        context_window=OLLAMA_CONTEXT_WINDOW,
    )
    await client.ensure_models([selected_text_model, selected_vision_model])

    analysis_directory = workspace / "analysis"
    reference_guidance = _reference_context(reference_files)
    (analysis_directory / "reference_guidance.txt").parent.mkdir(
        parents=True, exist_ok=True
    )
    (analysis_directory / "reference_guidance.txt").write_text(
        reference_guidance, encoding="utf-8"
    )
    page_text, image_manifest = render_analysis_inputs(
        filtered_pdf, selection, analysis_directory
    )
    await activity("inspecting_inputs")
    fragments: list[dict | list] = []
    fragment_directory = analysis_directory / "vision_fragments"
    fragment_directory.mkdir()
    inventory_path = analysis_directory / "source_inventory.json"
    for index, image_info in enumerate(image_manifest, start=1):
        image = Path(image_info["path"])
        await progress(25 + round(25 * index / len(image_manifest)))
        if process_callback is not None:
            await process_callback(
                f"Vision extraction {index}/{len(image_manifest)}: {image.name}"
            )
        fragment = await client.chat_json(
            selected_vision_model,
            build_vision_prompt(
                selection,
                image.name,
                index,
                len(image_manifest),
                source_text=image_info["text"],
                source_region=image_info["bbox"],
            ),
            images=[image],
            thinking_callback=process_callback,
            max_output_tokens=VISION_MAX_OUTPUT_TOKENS,
        )
        fragments.append(fragment)
        (fragment_directory / f"{index:02d}_{image.stem}.json").write_text(
            json.dumps(fragment, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        inventory_path.write_text(
            json.dumps(fragments, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    await activity("analyzing")
    await progress(55)
    cleaned_directory = analysis_directory / "cleaned_fragments"
    cleaned_directory.mkdir()
    cleaned_structures: list[dict] = []
    cleaned_by_fragment: list[dict | None] = [None] * len(fragments)
    meaningful_fragments = [
        (index, fragment)
        for index, fragment in enumerate(fragments, start=1)
        if isinstance(fragment, dict)
        and sum(
            len(fragment.get(key, []))
            for key in ("boards", "elements", "connections")
            if isinstance(fragment.get(key), list)
        )
        >= 2
    ]
    for position, (index, fragment) in enumerate(meaningful_fragments, start=1):
        if process_callback is not None:
            await process_callback(
                f"Fact cleanup {position}/{len(meaningful_fragments)}: crop {index}"
            )
        cleaned_result = await client.chat_json(
            selected_text_model,
            build_fragment_structure_prompt(
                fragment, f"crop {index}", reference_guidance
            ),
            thinking_callback=process_callback,
            max_output_tokens=VISION_MAX_OUTPUT_TOKENS,
        )
        cleaned = normalize_fragment(cleaned_result)
        invalid_connections = invalid_fragment_connections(cleaned)
        if invalid_connections:
            if process_callback is not None:
                await process_callback(
                    f"Endpoint repair for crop {index}: {len(invalid_connections)} invalid connection(s)"
                )
            repaired_result = await client.chat_json(
                selected_text_model,
                build_fragment_repair_prompt(cleaned, invalid_connections),
                thinking_callback=process_callback,
                max_output_tokens=VISION_MAX_OUTPUT_TOKENS,
            )
            repaired = normalize_fragment(repaired_result)
            if len(invalid_fragment_connections(repaired)) < len(invalid_connections):
                cleaned = repaired
        cleaned = materialize_connector_endpoints(cleaned)
        topology_result = await client.chat_json(
            selected_vision_model,
            build_topology_completion_prompt(cleaned, f"crop {index}"),
            images=[Path(image_manifest[index - 1]["path"])],
            thinking_callback=process_callback,
            max_output_tokens=VISION_MAX_OUTPUT_TOKENS,
        )
        cleaned = merge_fragment_connections(cleaned, topology_result)
        cleaned = materialize_connector_endpoints(cleaned)
        isolated_ids = isolated_physical_element_ids(cleaned)
        for batch_start in range(0, len(isolated_ids), 5):
            center_ids = isolated_ids[batch_start : batch_start + 5]
            if process_callback is not None:
                await process_callback(
                    f"Topology completion for crop {index}: {', '.join(center_ids)}"
                )
            targeted_prompt = build_topology_completion_prompt(
                cleaned, f"crop {index}"
            ) + (
                "\n\nFor this pass, return every visible connection touching at least "
                "one of these center element IDs: "
                + json.dumps(center_ids)
                + ". Trace all visible ports from each center; omit a center only when "
                "no line from it is visible."
            )
            targeted_result = await client.chat_json(
                selected_vision_model,
                targeted_prompt,
                images=[Path(image_manifest[index - 1]["path"])],
                thinking_callback=process_callback,
                max_output_tokens=VISION_MAX_OUTPUT_TOKENS,
            )
            cleaned = merge_fragment_connections(cleaned, targeted_result)
        cleaned_structures.append(cleaned)
        cleaned_by_fragment[index - 1] = cleaned
        (cleaned_directory / f"{index:02d}_structure.json").write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        await progress(50 + round(8 * position / len(meaningful_fragments)))
    structure = merge_structures(cleaned_structures)
    (analysis_directory / "architecture_structure.json").write_text(
        json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    await activity("compiling_connections")
    await progress(60)
    connections, unresolved_connections = compile_inventory_connections(
        structure, cleaned_by_fragment, cleaned_by_fragment
    )
    connection_result = {"connections": connections}
    architecture = compile_architecture(structure, connection_result)
    architecture = collapse_nonphysical_elements(architecture)
    connection_result = {"connections": architecture["connections"]}
    (analysis_directory / "architecture_connections.json").write_text(
        json.dumps(connection_result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (analysis_directory / "unresolved_connections.json").write_text(
        json.dumps(unresolved_connections, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    candidate = yaml.safe_dump(
        architecture, sort_keys=False, allow_unicode=True, width=100
    ).strip()
    (analysis_directory / "candidate.yml").write_text(candidate, encoding="utf-8")
    return candidate