from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def to_fts_query(text: str) -> str:
    tokens = tokenize(text)
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens)


def term_basis(token: str, dims: int) -> list[float]:
    seed = hashlib.sha256(token.encode("utf-8")).digest()
    basis = [0.0] * dims
    for index in range(dims):
        byte = seed[index % len(seed)]
        basis[index] = 1.0 if byte % 2 == 0 else -1.0
    return basis


@dataclass
class ChunkRecord:
    path: str
    title: str
    chunk_index: int
    start_line: int
    end_line: int
    text: str


def iter_source_files(source_dir: Path) -> Iterable[Path]:
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}:
            yield path


def infer_acl_groups(path: Path) -> list[str]:
    parts = {part.lower() for part in path.parts}
    groups = {"employees"}
    if "finance" in parts:
        groups.add("finance")
    if "hr" in parts:
        groups.add("hr")
    if "policies" in parts:
        groups.add("procurement")
    if "oracle" in parts:
        groups.update({"oracle", "dba"})
    return sorted(groups)


def load_source_document(path: Path) -> dict[str, object]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = str(payload.get("text", "")).strip()
        title = str(payload.get("title", path.stem)).strip() or path.stem
        citation_path = str(payload.get("source_uri", str(path.resolve())))
        acl_groups = [str(group) for group in payload.get("acl_groups", ["oracle", "dba"])]
        return {
            "text": text,
            "title": title,
            "citation_path": citation_path,
            "acl_groups": acl_groups,
        }

    raw_text = path.read_text(encoding="utf-8")
    title = raw_text.splitlines()[0].lstrip("# ").strip() if raw_text.splitlines() else path.stem
    return {
        "text": raw_text,
        "title": title,
        "citation_path": str(path.resolve()),
        "acl_groups": infer_acl_groups(path),
    }


def chunk_lines(text: str, chunk_size: int, chunk_overlap: int) -> list[tuple[int, int, str]]:
    lines = text.splitlines()
    if not lines:
        return []
    chunks: list[tuple[int, int, str]] = []
    step = max(1, chunk_size - chunk_overlap)
    for start in range(0, len(lines), step):
        end = min(len(lines), start + chunk_size)
        chunk_text = "\n".join(lines[start:end]).strip()
        if chunk_text:
            chunks.append((start + 1, end, chunk_text))
        if end == len(lines):
            break
    return chunks


class IndexBuilder:
    def __init__(self, source_dir: Path, index_dir: Path) -> None:
        self.source_dir = source_dir
        self.index_dir = index_dir
        self.sqlite_path = index_dir / "search.db"
        self.vector_path = index_dir / "vectors.json"

    def build(self, chunk_size: int = 10, chunk_overlap: int = 2) -> dict[str, int]:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if self.sqlite_path.exists():
            self.sqlite_path.unlink()

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        self._create_schema(conn)

        all_chunks: list[dict[str, object]] = []
        doc_count = 0
        for path in iter_source_files(self.source_dir):
            document = load_source_document(path)
            raw_text = str(document["text"])
            sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            title = str(document["title"])
            acl_groups = list(document["acl_groups"])
            citation_path = str(document["citation_path"])
            cursor = conn.execute(
                "insert into documents(path, title, sha256, acl_groups) values (?, ?, ?, ?)",
                (citation_path, title, sha256, json.dumps(acl_groups)),
            )
            document_id = cursor.lastrowid
            doc_count += 1
            for chunk_index, (start_line, end_line, chunk_text) in enumerate(
                chunk_lines(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            ):
                chunk_cursor = conn.execute(
                    """
                    insert into chunks(document_id, chunk_index, start_line, end_line, text)
                    values (?, ?, ?, ?, ?)
                    """,
                    (document_id, chunk_index, start_line, end_line, chunk_text),
                )
                chunk_id = chunk_cursor.lastrowid
                conn.execute(
                    "insert into chunks_fts(rowid, text) values (?, ?)",
                    (chunk_id, chunk_text),
                )
                all_chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "path": citation_path,
                        "title": title,
                        "acl_groups": acl_groups,
                        "chunk_index": chunk_index,
                        "start_line": start_line,
                        "end_line": end_line,
                        "text": chunk_text,
                    }
                )

        conn.commit()
        conn.close()

        vectors = self._build_vector_index(all_chunks)
        self.vector_path.write_text(json.dumps(vectors, indent=2), encoding="utf-8")
        return {"documents": doc_count, "chunks": len(all_chunks)}

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            create table documents (
                id integer primary key,
                path text not null unique,
                title text not null,
                sha256 text not null,
                acl_groups text not null
            );

            create table chunks (
                id integer primary key,
                document_id integer not null references documents(id),
                chunk_index integer not null,
                start_line integer not null,
                end_line integer not null,
                text text not null
            );

            create virtual table chunks_fts using fts5(
                text,
                content='chunks',
                content_rowid='id',
                tokenize='unicode61'
            );
            """
        )

    def _build_vector_index(self, chunks: list[dict[str, object]], dims: int = 128) -> dict[str, object]:
        doc_freq: Counter[str] = Counter()
        tokenized_chunks: dict[int, list[str]] = {}
        for chunk in chunks:
            chunk_id = int(chunk["chunk_id"])
            tokens = tokenize(str(chunk["text"]))
            tokenized_chunks[chunk_id] = tokens
            doc_freq.update(set(tokens))

        total_chunks = max(1, len(chunks))
        entries: list[dict[str, object]] = []
        for chunk in chunks:
            chunk_id = int(chunk["chunk_id"])
            counts = Counter(tokenized_chunks[chunk_id])
            vector = [0.0] * dims
            for token, count in counts.items():
                idf = math.log((1 + total_chunks) / (1 + doc_freq[token])) + 1.0
                weight = (1.0 + math.log(count)) * idf
                basis = term_basis(token, dims)
                for index, value in enumerate(basis):
                    vector[index] += weight * value
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            normalized = [value / norm for value in vector]
            entries.append(
                {
                    "chunk_id": chunk_id,
                    "vector": normalized,
                    "path": chunk["path"],
                    "title": chunk["title"],
                    "acl_groups": chunk["acl_groups"],
                    "chunk_index": chunk["chunk_index"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "text": chunk["text"],
                }
            )
        return {"dims": dims, "doc_freq": dict(doc_freq), "entries": entries, "total_chunks": total_chunks}

class HybridSearchEngine:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.sqlite_path = index_dir / "search.db"
        self.vector_path = index_dir / "vectors.json"
        self.conn = sqlite3.connect(self.sqlite_path)
        self.conn.row_factory = sqlite3.Row
        self.vector_index = json.loads(self.vector_path.read_text(encoding="utf-8"))

    def search(
        self,
        query: str,
        top_k: int = 5,
        acl_groups: list[str] | None = None,
    ) -> list[dict[str, object]]:
        bm25_hits = self._bm25_search(query, limit=max(top_k * 2, 6), acl_groups=acl_groups)
        vector_hits = self._vector_search(query, limit=max(top_k * 2, 6), acl_groups=acl_groups)
        fused = self._reciprocal_rank_fusion(bm25_hits, vector_hits)
        results: list[dict[str, object]] = []
        for rank, item in enumerate(fused[:top_k], start=1):
            citation = f"{item['path']}:{item['start_line']}-{item['end_line']}"
            results.append(
                {
                    "rank": rank,
                    "title": item["title"],
                    "score": round(float(item["score"]), 6),
                    "confidence": round(float(item["confidence"]), 6),
                    "bm25_rank": item.get("bm25_rank"),
                    "vector_rank": item.get("vector_rank"),
                    "acl_groups": item.get("acl_groups", []),
                    "citation": citation,
                    "chunk_index": item["chunk_index"],
                    "text": item["text"],
                }
            )
        return results

    def answer(
        self,
        query: str,
        top_k: int = 4,
        acl_groups: list[str] | None = None,
    ) -> dict[str, object]:
        results = self.search(query, top_k=top_k, acl_groups=acl_groups)
        evidence = results[: min(3, len(results))]
        if not evidence:
            return {"query": query, "answer": "No indexed evidence was found.", "citations": []}

        lines = []
        for item in evidence:
            sentence = self._best_sentence(item["text"], query)
            lines.append(sentence)

        unique_lines = []
        seen = set()
        for line in lines:
            if line not in seen:
                unique_lines.append(line)
                seen.add(line)

        answer_text = " ".join(unique_lines)
        return {
            "query": query,
            "answer": answer_text,
            "citations": [
                {
                    "title": item["title"],
                    "citation": item["citation"],
                    "score": item["score"],
                    "confidence": item["confidence"],
                }
                for item in evidence
            ],
            "evidence": evidence,
        }

    def _bm25_search(self, query: str, limit: int, acl_groups: list[str] | None) -> list[dict[str, object]]:
        fts_query = to_fts_query(query)
        if not fts_query:
            return []
        rows = self.conn.execute(
            """
            select
                chunks.id as chunk_id,
                documents.path as path,
                documents.title as title,
                documents.acl_groups as acl_groups,
                chunks.chunk_index as chunk_index,
                chunks.start_line as start_line,
                chunks.end_line as end_line,
                chunks.text as text,
                bm25(chunks_fts) as raw_score
            from chunks_fts
            join chunks on chunks.id = chunks_fts.rowid
            join documents on documents.id = chunks.document_id
            where chunks_fts match ?
            order by raw_score
            limit ?
            """,
            (fts_query, limit),
        ).fetchall()
        hits = []
        for rank, row in enumerate(rows, start=1):
            row_acl_groups = json.loads(row["acl_groups"])
            if not self._allowed(row_acl_groups, acl_groups):
                continue
            hits.append(
                {
                    "chunk_id": row["chunk_id"],
                    "path": row["path"],
                    "title": row["title"],
                    "acl_groups": row_acl_groups,
                    "chunk_index": row["chunk_index"],
                    "start_line": row["start_line"],
                    "end_line": row["end_line"],
                    "text": row["text"],
                    "score": 1.0 / (1.0 + abs(row["raw_score"])),
                    "bm25_rank": rank,
                }
            )
        return hits

    def _vector_search(self, query: str, limit: int, acl_groups: list[str] | None) -> list[dict[str, object]]:
        vector = self._query_vector(query)
        hits = []
        for entry in self.vector_index["entries"]:
            if not self._allowed(entry["acl_groups"], acl_groups):
                continue
            score = sum(a * b for a, b in zip(vector, entry["vector"], strict=True))
            hits.append(
                {
                    "chunk_id": entry["chunk_id"],
                    "path": entry["path"],
                    "title": entry["title"],
                    "acl_groups": entry["acl_groups"],
                    "chunk_index": entry["chunk_index"],
                    "start_line": entry["start_line"],
                    "end_line": entry["end_line"],
                    "text": entry["text"],
                    "score": score,
                }
            )
        hits.sort(key=lambda item: item["score"], reverse=True)
        for rank, hit in enumerate(hits[:limit], start=1):
            hit["vector_rank"] = rank
        return hits[:limit]

    def _query_vector(self, query: str) -> list[float]:
        dims = int(self.vector_index["dims"])
        doc_freq = self.vector_index["doc_freq"]
        total_chunks = int(self.vector_index["total_chunks"])
        counts = Counter(tokenize(query))
        vector = [0.0] * dims
        for token, count in counts.items():
            df = int(doc_freq.get(token, 0))
            idf = math.log((1 + total_chunks) / (1 + df)) + 1.0
            weight = (1.0 + math.log(count)) * idf
            basis = term_basis(token, dims)
            for index, value in enumerate(basis):
                vector[index] += weight * value
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _reciprocal_rank_fusion(
        self,
        bm25_hits: list[dict[str, object]],
        vector_hits: list[dict[str, object]],
        k: int = 60,
    ) -> list[dict[str, object]]:
        merged: dict[int, dict[str, object]] = {}
        for hits, key in ((bm25_hits, "bm25_rank"), (vector_hits, "vector_rank")):
            for hit in hits:
                chunk_id = int(hit["chunk_id"])
                current = merged.setdefault(
                    chunk_id,
                    {
                        "chunk_id": hit["chunk_id"],
                        "path": hit["path"],
                        "title": hit["title"],
                        "acl_groups": hit.get("acl_groups", []),
                        "chunk_index": hit["chunk_index"],
                        "start_line": hit["start_line"],
                        "end_line": hit["end_line"],
                        "text": hit["text"],
                        "score": 0.0,
                    },
                )
                rank = int(hit.get(key) or 0)
                current[key] = rank or None
                current["score"] = float(current.get("score", 0.0)) + (1.0 / (k + max(rank, 1)))
        for item in merged.values():
            item["confidence"] = self._confidence(item)
        ranked = sorted(merged.values(), key=lambda item: item["score"], reverse=True)
        return ranked

    def _best_sentence(self, text: str, query: str) -> str:
        query_terms = set(tokenize(query))
        candidates = re.split(r"(?<=[.!?])\s+", text.strip())
        scored = []
        for sentence in candidates:
            terms = set(tokenize(sentence))
            overlap = len(query_terms & terms)
            scored.append((overlap, len(sentence), sentence))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return scored[0][2] if scored else text.strip()

    def _allowed(self, row_acl_groups: list[str], acl_groups: list[str] | None) -> bool:
        if not acl_groups:
            return True
        requested = {group.lower() for group in acl_groups}
        actual = {group.lower() for group in row_acl_groups}
        return bool(requested & actual)

    def _confidence(self, item: dict[str, object]) -> float:
        bm25_rank = item.get("bm25_rank")
        vector_rank = item.get("vector_rank")
        if bm25_rank and vector_rank:
            return min(1.0, 0.55 + (1.0 / (bm25_rank + vector_rank)))
        if bm25_rank or vector_rank:
            return 0.4
        return 0.2
