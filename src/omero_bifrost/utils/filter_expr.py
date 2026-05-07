"""Parser for deterministic key:value filter expressions."""

from __future__ import annotations

from dataclasses import dataclass


class FilterParseError(ValueError):
    def __init__(self, message: str, *, expr: str):
        super().__init__(message)
        self.expr = expr


@dataclass(frozen=True)
class FilterExpr:
    key: str
    op: str
    value: str


def parse_filter_expr(expr: str) -> FilterExpr:
    """Parse legacy key:value expressions and map them to equality semantics."""
    s = expr.strip()
    if not s:
        raise FilterParseError("empty expression", expr=expr)
    if ":" not in s:
        raise FilterParseError("invalid filter expression, expected 'key:value'", expr=expr)

    key, value = s.split(":", 1)
    key = key.strip()
    value = value.strip()

    if not key:
        raise FilterParseError("missing key", expr=expr)
    if value == "":
        raise FilterParseError("missing value", expr=expr)

    return FilterExpr(key=key, op="=", value=value)


def parse_filter_exprs(exprs: list[str]) -> list[FilterExpr]:
    return [parse_filter_expr(e) for e in exprs]
