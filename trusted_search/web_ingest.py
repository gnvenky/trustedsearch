from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


WHITESPACE_RE = re.compile(r"\s+")


class OracleHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "noscript", "svg"}
        self.links: list[str] = []
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._skip_tags:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        if tag in {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._skip_tags and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        cleaned = WHITESPACE_RE.sub(" ", data).strip()
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
        self.text_parts.append(cleaned)


@dataclass
class CrawledDocument:
    url: str
    title: str
    text: str
    source_type: str
    tags: list[str]


def _normalize_text(text: str) -> str:
    lines = [WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    normalized = parsed._replace(fragment="", query="")
    if normalized.scheme and normalized.netloc:
        return normalized.geturl()
    return url


def _slug(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _allowed(url: str, allow_domains: list[str], allow_prefixes: list[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.lower()
    if allow_domains and host not in {domain.lower() for domain in allow_domains}:
        return False
    if allow_prefixes and not any(url.startswith(prefix) for prefix in allow_prefixes):
        return False
    return True


def fetch_html(url: str, timeout: int = 20) -> tuple[str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "trusted-search-oracle-ingestor/0.1",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset, errors="replace")
        return response.geturl(), html


def parse_html(html: str) -> tuple[str, str, list[str]]:
    parser = OracleHtmlParser()
    parser.feed(html)
    title = " ".join(parser.title_parts).strip()
    text = _normalize_text(" ".join(parser.text_parts))
    links = parser.links
    return title, text, links


def crawl_group(group: dict[str, object], output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    allow_domains = list(group.get("allow_domains", []))
    allow_prefixes = list(group.get("allow_prefixes", []))
    max_pages = int(group.get("max_pages", 10))
    source_type = str(group.get("source_type", "web"))
    tags = [str(tag) for tag in group.get("tags", [])]
    queue = deque(_normalize_url(url) for url in group.get("seed_urls", []))
    seen: set[str] = set()
    written = 0
    failed = 0

    while queue and written < max_pages:
        url = queue.popleft()
        if url in seen or not _allowed(url, allow_domains, allow_prefixes):
            continue
        seen.add(url)
        try:
            final_url, html = fetch_html(url)
        except (HTTPError, URLError, TimeoutError, ValueError):
            failed += 1
            continue
        title, text, links = parse_html(html)
        if len(text.split()) < 80:
            continue
        document = {
            "title": title or final_url,
            "text": text,
            "source_uri": final_url,
            "source_type": source_type,
            "tags": tags,
            "acl_groups": ["oracle", "dba"],
        }
        document_path = output_dir / f"{_slug(final_url)}.json"
        document_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
        written += 1

        for link in links:
            absolute = _normalize_url(urljoin(final_url, link))
            if absolute not in seen and _allowed(absolute, allow_domains, allow_prefixes):
                queue.append(absolute)

    return {"documents": written, "discovered": len(seen), "failed": failed}


def crawl_manifest(manifest_path: Path, output_dir: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    groups = manifest.get("groups", [])
    totals = {"groups": 0, "documents": 0}
    group_results: list[dict[str, object]] = []
    for group in groups:
        group_name = str(group.get("name", "unnamed"))
        group_dir = output_dir / group_name
        stats = crawl_group(group, group_dir)
        totals["groups"] += 1
        totals["documents"] += int(stats["documents"])
        group_results.append({"group": group_name, **stats})
    return {"summary": totals, "groups": group_results}
