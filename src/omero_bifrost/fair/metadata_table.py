from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv

REQUIRED_COL = "IMAGE_DATA_PATH"
CONTROL_COLS = {"SAMPLE_ID", "OMERO_TAGS", "ETL_TAG", REQUIRED_COL}
IMAGE_EXTS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".ome.tiff"}


class MetadataTableError(ValueError):
    pass


@dataclass(frozen=True)
class ExpandedRow:
    row_index: int
    image_path: str
    metadata: dict


def load_metadata_table(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if REQUIRED_COL not in (reader.fieldnames or []):
            raise MetadataTableError(f"missing required column: {REQUIRED_COL}")
        return list(reader)


def expand_rows(rows: list[dict[str, str]]) -> list[ExpandedRow]:
    out: list[ExpandedRow] = []
    seen: dict[str, int] = {}
    for idx, row in enumerate(rows, start=2):
        p = Path(row[REQUIRED_COL]).expanduser()
        if not p.exists():
            raise MetadataTableError(f"row {idx}: unresolved path '{p}'")
        targets: list[Path]
        if p.is_dir():
            targets = sorted([x for x in p.iterdir() if x.is_file() and x.suffix.lower() in IMAGE_EXTS])
        else:
            targets = [p]
        md = {k: v for k, v in row.items() if k not in CONTROL_COLS and v not in (None, "")}
        for t in targets:
            key = str(t.resolve())
            if key in seen and md != out[seen[key]].metadata:
                raise MetadataTableError(f"row {idx}: conflict for path '{key}'")
            seen[key] = len(out)
            out.append(ExpandedRow(row_index=idx, image_path=key, metadata=md))
    return out
