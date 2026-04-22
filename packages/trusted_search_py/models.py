"""Shared data model scaffolding."""

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    title: str
    citation: str
    score: float
    confidence: float
    acl_groups: list[str] = field(default_factory=list)
    text: str = ""
