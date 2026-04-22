"""Configuration helpers for the Python layout."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    index_dir: Path = Path(os.environ.get("TRUSTED_SEARCH_INDEX_DIR", ROOT / "data" / "index"))
    source_dir: Path = Path(os.environ.get("TRUSTED_SEARCH_SOURCE_DIR", ROOT / "sample_sources"))
    host: str = os.environ.get("TRUSTED_SEARCH_HOST", "127.0.0.1")
    port: int = int(os.environ.get("TRUSTED_SEARCH_PORT", "3000"))
