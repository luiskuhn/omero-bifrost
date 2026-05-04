import json
from dataclasses import asdict


def records_to_jsonl(records):
    return "\n".join(json.dumps(asdict(r), sort_keys=True) for r in records)
