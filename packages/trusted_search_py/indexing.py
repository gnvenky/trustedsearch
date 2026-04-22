"""Index-building scaffolding."""

from pathlib import Path


class IndexBuilder:
    def __init__(self, source_dir: Path, index_dir: Path) -> None:
        self.source_dir = source_dir
        self.index_dir = index_dir

