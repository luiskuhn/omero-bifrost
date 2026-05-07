"""Federation execution runner and provenance modeling."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable, Iterable
import json
import time
import uuid

FAILURE_CATEGORIES = {
    "PermissionError": "auth",
    "AuthenticationError": "auth",
    "FilterParseError": "validation",
    "ValueError": "validation",
    "TimeoutError": "transient_network",
    "ConnectionError": "transient_network",
}


def categorize_failure(exc: Exception) -> str:
    if exc.__class__.__name__ in FAILURE_CATEGORIES:
        return FAILURE_CATEGORIES[exc.__class__.__name__]
    text = str(exc).lower()
    if "group" in text and "scope" in text:
        return "group_scope"
    if "timeout" in text or "tempor" in text or "network" in text:
        return "transient_network"
    if "auth" in text or "permission" in text or "credential" in text:
        return "auth"
    if "invalid" in text or "parse" in text or "schema" in text:
        return "validation"
    return "unexpected"


@dataclass(frozen=True)
class ProvenanceEnvelope:
    provenance_id: str
    timestamp_utc: str
    tool_version: str
    command: str
    sanitized_args: dict[str, str]
    effective_profile: str | None
    effective_host: str | None
    effective_group: str | None
    fail_policy: str
    timeout_seconds: int
    retries: int
    backoff_seconds: float
    input_checksums: dict[str, str]


@dataclass(frozen=True)
class FederationRecord:
    server_profile: str
    server_host: str
    operation: str
    status: str
    local_object_id: str | None = None
    federated_object_id: str | None = None
    object_type: str | None = None
    error_category: str | None = None
    error_message: str | None = None
    message: str | None = None
    provenance_id: str | None = None


class FederationRunner:
    def __init__(self, max_workers: int = 4, timeout_seconds: int = 300, fail_policy: str = "continue", retries: int = 0, backoff_seconds: float = 0.5):
        self.max_workers = max(1, int(max_workers))
        self.timeout_seconds = int(timeout_seconds)
        self.fail_policy = fail_policy
        self.retries = max(0, int(retries))
        self.backoff_seconds = float(backoff_seconds)

    def run(self, profiles: Iterable[str], operation: str, fn: Callable[[str], list[FederationRecord]], *, args: dict[str, str] | None = None, input_artifacts: list[str] | None = None):
        profiles = sorted(set(profiles))
        run_id = str(uuid.uuid4())
        provenance = self._build_provenance(run_id, operation, profiles, args or {}, input_artifacts or [])
        per_profile = {}
        merged: list[FederationRecord] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            fut_map = {ex.submit(self._run_one, p, fn): p for p in profiles}
            for fut in as_completed(fut_map, timeout=self.timeout_seconds):
                profile = fut_map[fut]
                try:
                    records = [self._ensure_record_shape(r, operation, provenance.provenance_id) for r in fut.result()]
                    per_profile[profile] = {"status": "ok", "count": len(records), "fail_policy": self.fail_policy}
                    merged.extend(records)
                except Exception as exc:
                    category = categorize_failure(exc)
                    per_profile[profile] = {"status": "error", "error": str(exc), "error_category": category, "fail_policy": self.fail_policy}
                    merged.append(FederationRecord(profile, "unknown", operation, "error", error_category=category, error_message=str(exc), message=str(exc), provenance_id=provenance.provenance_id))
                    if self.fail_policy == "fail-fast":
                        break
        merged_sorted = sorted(merged, key=lambda r: (r.server_profile, r.operation, r.object_type or "", r.local_object_id or "", r.federated_object_id or "", r.status, r.message or ""))
        return {"profiles": per_profile, "records": merged_sorted, "provenance": provenance}

    def _run_one(self, profile, fn):
        delay = self.backoff_seconds
        last_exc = None
        for i in range(self.retries + 1):
            try:
                return fn(profile)
            except Exception as exc:
                last_exc = exc
                if i < self.retries:
                    time.sleep(delay)
                    delay *= 2
        raise last_exc

    def _build_provenance(self, run_id: str, command: str, profiles: list[str], args: dict[str, str], input_artifacts: list[str]) -> ProvenanceEnvelope:
        checksums = {}
        for path in sorted(set(input_artifacts)):
            p = Path(path)
            if p.exists() and p.is_file():
                checksums[path] = sha256(p.read_bytes()).hexdigest()
        return ProvenanceEnvelope(
            provenance_id=run_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            tool_version="omero-bifrost/1",
            command=command,
            sanitized_args={k: "***" if "password" in k.lower() else str(v) for k, v in sorted(args.items())},
            effective_profile=",".join(profiles) if profiles else None,
            effective_host=None,
            effective_group=None,
            fail_policy=self.fail_policy,
            timeout_seconds=self.timeout_seconds,
            retries=self.retries,
            backoff_seconds=self.backoff_seconds,
            input_checksums=checksums,
        )

    def _ensure_record_shape(self, record: FederationRecord, operation: str, provenance_id: str) -> FederationRecord:
        category = record.error_category
        if record.status == "error" and not category:
            category = "unexpected"
        return FederationRecord(
            server_profile=record.server_profile,
            server_host=record.server_host,
            operation=operation,
            status=record.status,
            local_object_id=record.local_object_id,
            federated_object_id=record.federated_object_id,
            object_type=record.object_type,
            error_category=category,
            error_message=record.error_message,
            message=record.message or record.error_message or record.status,
            provenance_id=provenance_id,
        )
