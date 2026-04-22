from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trusted_search.engine import IndexBuilder


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the trusted search indexes from source files.")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "sample_sources")
    parser.add_argument("--index-dir", type=Path, default=ROOT / "data" / "index")
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--chunk-overlap", type=int, default=2)
    args = parser.parse_args()

    stats = IndexBuilder(args.source_dir, args.index_dir).build(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
