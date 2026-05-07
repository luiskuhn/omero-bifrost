"""Ontology normalization helpers (currently NCIT-focused)."""

from __future__ import annotations

import re

PREFIX_MAP = {
    "NCIT": "http://purl.obolibrary.org/obo/NCIT_",
}

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*:[A-Za-z0-9_\-]+$")


def normalize_term(value: str) -> tuple[str | None, str | None]:
    if not isinstance(value, str):
        return None, "invalid_value_type"
    raw = value.strip()
    if not raw:
        return None, "malformed_id"

    if raw.startswith("http://") or raw.startswith("https://"):
        if "NCIT_" in raw:
            code = raw.rsplit("NCIT_", 1)[-1]
            return f"NCIT:{code}", None
        return None, "unknown_term"

    if ID_RE.match(raw):
        prefix, local = raw.split(":", 1)
        if prefix not in PREFIX_MAP:
            return None, "unmapped_prefix"
        return f"{prefix}:{local}", None

    if raw.startswith("C") and raw[1:].isdigit():
        return f"NCIT:{raw}", None

    return None, "malformed_id"
