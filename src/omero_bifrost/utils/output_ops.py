"""Output serialization helpers for CLI/federation results."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _to_obj(item: Any) -> Any:
    """Convert dataclasses to plain serializable objects."""
    return asdict(item) if is_dataclass(item) else item


def records_to_jsonl(records: list[Any]) -> str:
    """Serialize records to deterministic JSON Lines output."""
    return "\n".join(json.dumps(_to_obj(r), sort_keys=True) for r in records)


def serialize_execution_output(execution_result: dict[str, Any]) -> str:
    """Serialize normalized command output with stable key ordering."""
    payload = {
        "provenance": _to_obj(execution_result.get("provenance")),
        "profiles": execution_result.get("profiles", {}),
        "records": [_to_obj(r) for r in execution_result.get("records", [])],
    }
    return json.dumps(payload, sort_keys=True)
