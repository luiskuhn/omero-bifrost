"""Subprocess execution and output parsing for OMERO CLI commands."""

from __future__ import annotations

from dataclasses import dataclass, field
import subprocess
from typing import Any


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    cmd: list[str]
    artifacts: dict[str, Any] = field(default_factory=dict)


class OmeroCliError(RuntimeError):
    """Base exception for OMERO CLI command errors."""


class OmeroCliCommandError(OmeroCliError):
    def __init__(self, message: str, result: CommandResult):
        super().__init__(message)
        self.result = result


class OmeroCliParseError(OmeroCliError):
    def __init__(self, message: str, result: CommandResult | None = None):
        super().__init__(message)
        self.result = result


def _redact_cmd(args: list[str]) -> list[str]:
    redacted = list(args)
    for i, token in enumerate(redacted[:-1]):
        if token in {"-w", "--password"}:
            redacted[i + 1] = "***"
    return redacted


def run_omero_cli(args: list[str], *, redact: bool = True) -> CommandResult:
    cmd = _redact_cmd(args) if redact else list(args)
    completed = subprocess.run(
        args,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    result = CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        cmd=cmd,
    )
    if completed.returncode != 0:
        raise OmeroCliCommandError(
            f"OMERO CLI command failed with exit code {completed.returncode}: {' '.join(cmd)}",
            result,
        )
    return result


def _parse_prefixed_value(result: CommandResult, prefix: str) -> str:
    for line in result.stdout.splitlines():
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if value:
                return value
            break
    raise OmeroCliParseError(
        f"Unable to parse expected prefix '{prefix}' from command output.",
        result,
    )


def parse_image_ids(result: CommandResult) -> list[str]:
    raw = _parse_prefixed_value(result, "Image:")
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise OmeroCliParseError("Image output line exists but had no IDs.", result)
    return values


def parse_original_file_id(result: CommandResult) -> str:
    return _parse_prefixed_value(result, "OriginalFile:")


def parse_tag_annotation_id(result: CommandResult) -> int:
    raw = _parse_prefixed_value(result, "TagAnnotation:")
    try:
        return int(raw)
    except ValueError as exc:
        raise OmeroCliParseError(f"TagAnnotation ID is not an integer: {raw}", result) from exc


def parse_file_annotation_id(result: CommandResult) -> str:
    return _parse_prefixed_value(result, "FileAnnotation:")


def parse_image_annotation_link_id(result: CommandResult) -> str:
    return _parse_prefixed_value(result, "ImageAnnotationLink:")
