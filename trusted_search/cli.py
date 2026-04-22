from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import HybridSearchEngine, IndexBuilder
from .web_ingest import crawl_manifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trusted hybrid search")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build indexes from source files")
    build_parser.add_argument("--source-dir", type=Path, required=True)
    build_parser.add_argument("--index-dir", type=Path, required=True)
    build_parser.add_argument("--chunk-size", type=int, default=10)
    build_parser.add_argument("--chunk-overlap", type=int, default=2)

    fetch_parser = subparsers.add_parser("fetch-web", help="Fetch web pages from a manifest into a local corpus")
    fetch_parser.add_argument("--manifest", type=Path, required=True)
    fetch_parser.add_argument("--output-dir", type=Path, required=True)

    oracle_parser = subparsers.add_parser("build-oracle", help="Fetch Oracle public sources and build an index")
    oracle_parser.add_argument("--manifest", type=Path, required=True)
    oracle_parser.add_argument("--corpus-dir", type=Path, required=True)
    oracle_parser.add_argument("--index-dir", type=Path, required=True)
    oracle_parser.add_argument("--chunk-size", type=int, default=14)
    oracle_parser.add_argument("--chunk-overlap", type=int, default=3)

    search_parser = subparsers.add_parser("search", help="Run hybrid search")
    search_parser.add_argument("query")
    search_parser.add_argument("--index-dir", type=Path, required=True)
    search_parser.add_argument("--top-k", type=int, default=5)
    search_parser.add_argument("--acl-group", action="append", dest="acl_groups")

    answer_parser = subparsers.add_parser("answer", help="Generate a grounded answer from retrieved chunks")
    answer_parser.add_argument("query")
    answer_parser.add_argument("--index-dir", type=Path, required=True)
    answer_parser.add_argument("--top-k", type=int, default=4)
    answer_parser.add_argument("--acl-group", action="append", dest="acl_groups")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "build":
        builder = IndexBuilder(args.source_dir, args.index_dir)
        stats = builder.build(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
        print(json.dumps(stats, indent=2))
        return 0

    if args.command == "fetch-web":
        stats = crawl_manifest(args.manifest, args.output_dir)
        print(json.dumps(stats, indent=2))
        return 0

    if args.command == "build-oracle":
        fetch_stats = crawl_manifest(args.manifest, args.corpus_dir)
        build_stats = IndexBuilder(args.corpus_dir, args.index_dir).build(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        print(json.dumps({"fetch": fetch_stats, "build": build_stats}, indent=2))
        return 0

    engine = HybridSearchEngine(args.index_dir)
    if args.command == "search":
        results = engine.search(args.query, top_k=args.top_k, acl_groups=args.acl_groups)
        print(json.dumps(results, indent=2))
        return 0

    if args.command == "answer":
        answer = engine.answer(args.query, top_k=args.top_k, acl_groups=args.acl_groups)
        print(json.dumps(answer, indent=2))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2
