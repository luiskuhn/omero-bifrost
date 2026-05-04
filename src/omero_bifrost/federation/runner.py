from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable
import time

@dataclass(frozen=True)
class FederationRecord:
    server_profile: str
    server_host: str
    operation: str
    status: str
    local_object_id: str | None = None
    federated_object_id: str | None = None
    object_type: str | None = None
    error_type: str | None = None
    error_message: str | None = None

class FederationRunner:
    def __init__(self, max_workers: int = 4, timeout_seconds: int = 300, fail_policy: str = "continue", retries: int = 0, backoff_seconds: float = 0.5):
        self.max_workers = max(1, int(max_workers))
        self.timeout_seconds = int(timeout_seconds)
        self.fail_policy = fail_policy
        self.retries = max(0, int(retries))
        self.backoff_seconds = float(backoff_seconds)

    def run(self, profiles: Iterable[str], operation: str, fn: Callable[[str], list[FederationRecord]]):
        profiles = sorted(set(profiles))
        per_profile = {}
        merged: list[FederationRecord] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            fut_map = {ex.submit(self._run_one, p, fn): p for p in profiles}
            for fut in as_completed(fut_map, timeout=self.timeout_seconds):
                profile = fut_map[fut]
                try:
                    records = fut.result()
                    per_profile[profile] = {"status": "ok", "count": len(records)}
                    merged.extend(records)
                except Exception as exc:
                    per_profile[profile] = {"status": "error", "error": str(exc), "error_type": exc.__class__.__name__}
                    merged.append(FederationRecord(profile, "unknown", operation, "error", error_type=exc.__class__.__name__, error_message=str(exc)))
                    if self.fail_policy == "fail-fast":
                        break
        merged_sorted = sorted(merged, key=lambda r: (r.server_profile, r.operation, r.object_type or "", r.local_object_id or "", r.federated_object_id or "", r.status))
        return {"profiles": per_profile, "records": merged_sorted}

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
