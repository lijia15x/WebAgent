import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf


FIGURE_CAPTION_PATTERN = re.compile(
    r"^Figure\s+\d+(?:-\d+)+[\.:]?\s*(?P<title>.+)$",
    re.IGNORECASE,
)
PRODUCT_NOISE_PATTERN = re.compile(
    r"\b(?:modular|smbus|architecture|diagram)\b",
    re.IGNORECASE,
)
MAX_FIGURE_CAPTIONS_PER_CONTENT_PAGE = 3


class ArchitectureFigureNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ArchitectureFigure:
    page_number: int
    caption: str
    product_name: str
    modular: bool


@dataclass(frozen=True)
class ArchitectureSelection:
    product_name: str
    target: ArchitectureFigure
    figures: tuple[ArchitectureFigure, ...]


def _product_name(title: str) -> str:
    product = " ".join(PRODUCT_NOISE_PATTERN.sub(" ", title).split())
    return product.strip(" .:-") or "Unnamed platform"


def _find_candidates(document: pymupdf.Document) -> list[ArchitectureFigure]:
    candidates: list[ArchitectureFigure] = []
    for page_index, page in enumerate(document):
        captions: list[tuple[str, str]] = []
        for raw_line in page.get_text("text").splitlines():
            line = " ".join(raw_line.split())
            match = FIGURE_CAPTION_PATTERN.match(line)
            if match:
                captions.append((line, match.group("title")))

        # Figure lists and tables of contents contain many captions but no diagram.
        if len(captions) > MAX_FIGURE_CAPTIONS_PER_CONTENT_PAGE:
            continue

        for caption, title in captions:
            normalized = title.casefold()
            if "smbus" not in normalized or "architecture" not in normalized:
                continue
            candidates.append(
                ArchitectureFigure(
                    page_number=page_index + 1,
                    caption=caption,
                    product_name=_product_name(title),
                    modular="modular" in normalized,
                )
            )
    return candidates


def extract_architecture_pages(
    source_pdf: Path,
    output_pdf: Path,
) -> ArchitectureSelection:
    try:
        source = pymupdf.open(source_pdf)
    except Exception as exc:
        raise ArchitectureFigureNotFoundError(
            f"Unable to read architecture PDF: {exc}"
        ) from exc

    try:
        candidates = _find_candidates(source)
        if not candidates:
            raise ArchitectureFigureNotFoundError(
                "No Figure caption containing both SMBus and Architecture was found"
            )

        target = next(
            (candidate for candidate in candidates if candidate.modular),
            candidates[0],
        )
        family = target.product_name.casefold()
        selected = tuple(
            candidate
            for candidate in candidates
            if candidate.product_name.casefold() == family
        )

        reduced = pymupdf.open()
        try:
            for figure in selected:
                page_index = figure.page_number - 1
                reduced.insert_pdf(source, from_page=page_index, to_page=page_index)
            reduced.save(output_pdf)
        finally:
            reduced.close()
    finally:
        source.close()

    return ArchitectureSelection(
        product_name=target.product_name,
        target=target,
        figures=selected,
    )
