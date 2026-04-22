"""Connector and ingestion scaffolding."""

from pathlib import Path


class SourceConnector:
    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir

