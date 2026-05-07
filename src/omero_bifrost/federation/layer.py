"""Federation layer abstractions for cross-profile operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .runner import FederationRecord, FederationRunner


@dataclass(frozen=True)
class PullTarget:
    server_profile: str
    target_id: str
    target_type: str


def federated_query(
    profiles: Iterable[str],
    query_fn: Callable[[str], list[FederationRecord]],
    *,
    fail_policy: str = "continue",
):
    """Run the same query across all selected OMERO server profiles."""
    runner = FederationRunner(fail_policy=fail_policy)
    return runner.run(profiles, "query", query_fn)


def federated_push(
    profiles: Iterable[str],
    push_fn: Callable[[str], list[FederationRecord]],
    *,
    fail_policy: str = "continue",
):
    """Push to valid target(s) in selected OMERO server profiles."""
    runner = FederationRunner(fail_policy=fail_policy)
    return runner.run(profiles, "push", push_fn)


def federated_annotate(
    profiles: Iterable[str],
    annotate_fn: Callable[[str], list[FederationRecord]],
    *,
    fail_policy: str = "continue",
):
    """Apply metadata annotations at scale to targets across many OMERO server profiles."""
    runner = FederationRunner(fail_policy=fail_policy)
    return runner.run(profiles, "annotate", annotate_fn)


def federated_pull(
    targets: Iterable[PullTarget],
    pull_fn: Callable[[PullTarget], list[FederationRecord]],
    *,
    fail_policy: str = "continue",
):
    """Pull objects where each target explicitly declares its hosting OMERO server profile."""
    runner = FederationRunner(fail_policy=fail_policy)

    target_list = list(targets)
    grouped: dict[str, list[PullTarget]] = {}
    for target in target_list:
        grouped.setdefault(target.server_profile, []).append(target)

    def _per_profile(profile: str):
        records: list[FederationRecord] = []
        for target in grouped.get(profile, []):
            records.extend(pull_fn(target))
        return records

    return runner.run(sorted(grouped.keys()), "pull", _per_profile)
