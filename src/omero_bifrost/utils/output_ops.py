import json
from dataclasses import asdict, is_dataclass


def _to_obj(item):
    if is_dataclass(item):
        return asdict(item)
    return item


def records_to_jsonl(records):
    return "\n".join(json.dumps(_to_obj(r), sort_keys=True) for r in records)


def serialize_execution_output(execution_result: dict) -> str:
    payload = {
        "provenance": _to_obj(execution_result.get("provenance")),
        "profiles": execution_result.get("profiles", {}),
        "records": [_to_obj(r) for r in execution_result.get("records", [])],
    }
    return json.dumps(payload, sort_keys=True)
