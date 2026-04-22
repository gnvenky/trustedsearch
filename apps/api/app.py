from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trusted_search.engine import HybridSearchEngine


INDEX_OPTIONS = {
    "sample": ROOT / "data" / "index",
    "oracle": ROOT / "data" / "oracle_index",
}

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trusted Search Q&A</title>
  <style>
    :root {
      --bg: #f4efe7;
      --panel: rgba(255, 251, 245, 0.92);
      --ink: #1f2933;
      --muted: #5d6b78;
      --accent: #b4492d;
      --accent-2: #214e62;
      --line: rgba(31, 41, 51, 0.12);
      --shadow: 0 18px 50px rgba(49, 41, 31, 0.14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(180, 73, 45, 0.18), transparent 28%),
        radial-gradient(circle at 85% 18%, rgba(33, 78, 98, 0.17), transparent 24%),
        linear-gradient(180deg, #f7f1e7 0%, #efe6d8 100%);
      min-height: 100vh;
    }
    .shell {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: grid;
      gap: 18px;
      margin-bottom: 24px;
    }
    .eyebrow {
      font-size: 0.8rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--accent);
      font-weight: 700;
    }
    h1 {
      margin: 0;
      font-size: clamp(2.2rem, 5vw, 4.3rem);
      line-height: 0.95;
      font-weight: 600;
      max-width: 10ch;
    }
    .subhead {
      max-width: 60ch;
      font-size: 1.03rem;
      line-height: 1.6;
      color: var(--muted);
    }
    .grid {
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.85fr);
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }
    .ask {
      padding: 24px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      font-weight: 700;
    }
    textarea, select, input, button {
      font: inherit;
    }
    textarea {
      width: 100%;
      min-height: 148px;
      resize: vertical;
      border-radius: 18px;
      border: 1px solid var(--line);
      padding: 16px 18px;
      background: rgba(255, 255, 255, 0.75);
      color: var(--ink);
    }
    .controls {
      display: grid;
      grid-template-columns: 1fr 130px 160px;
      gap: 12px;
      margin-top: 14px;
      align-items: end;
    }
    select, input {
      width: 100%;
      border-radius: 14px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.78);
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 14px 18px;
      background: linear-gradient(135deg, var(--accent), #d16b44);
      color: white;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, box-shadow 120ms ease;
      box-shadow: 0 14px 26px rgba(180, 73, 45, 0.25);
    }
    button:hover { transform: translateY(-1px); }
    button:disabled {
      cursor: wait;
      opacity: 0.7;
      transform: none;
    }
    .side {
      padding: 22px;
      display: grid;
      gap: 14px;
      align-content: start;
    }
    .note {
      border-radius: 16px;
      padding: 14px 16px;
      background: rgba(33, 78, 98, 0.08);
      border: 1px solid rgba(33, 78, 98, 0.12);
    }
    .note strong {
      display: block;
      margin-bottom: 6px;
      color: var(--accent-2);
      font-size: 0.95rem;
    }
    .answer-card, .result-card {
      padding: 20px 22px;
      margin-top: 18px;
    }
    .answer-text {
      font-size: 1.05rem;
      line-height: 1.7;
      white-space: pre-wrap;
    }
    .citations, .results {
      display: grid;
      gap: 12px;
      margin-top: 16px;
    }
    .citation, .result {
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }
    .title-row {
      display: flex;
      gap: 10px;
      align-items: baseline;
      justify-content: space-between;
      flex-wrap: wrap;
    }
    .doc-title {
      font-weight: 700;
    }
    .meta {
      color: var(--muted);
      font-size: 0.9rem;
    }
    a {
      color: var(--accent-2);
      word-break: break-all;
    }
    .empty, .error {
      padding: 18px 22px;
      margin-top: 18px;
    }
    .error {
      border-color: rgba(180, 73, 45, 0.28);
      background: rgba(180, 73, 45, 0.08);
    }
    .loading {
      color: var(--muted);
      margin-top: 14px;
      font-style: italic;
    }
    @media (max-width: 860px) {
      .grid { grid-template-columns: 1fr; }
      .controls { grid-template-columns: 1fr; }
      h1 { max-width: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">Trusted Search</div>
      <h1>Ask protection questions and inspect the evidence.</h1>
      <div class="subhead">
        This interface runs against your local BM25 + vector index and shows grounded citations for every answer.
        Use the Oracle corpus for RMAN and ZDLRA questions, or the sample corpus for a lightweight smoke test.
      </div>
    </section>

    <section class="grid">
      <div>
        <div class="panel ask">
          <label for="question">Question</label>
          <textarea id="question" placeholder="What are Oracle best practices for RMAN with Recovery Appliance?"></textarea>
          <div class="controls">
            <div>
              <label for="index-key">Corpus</label>
              <select id="index-key">
                <option value="oracle">Oracle public docs</option>
                <option value="sample">Sample local corpus</option>
              </select>
            </div>
            <div>
              <label for="top-k">Top K</label>
              <input id="top-k" type="number" min="1" max="10" value="5">
            </div>
            <button id="ask-button" type="button">Ask</button>
          </div>
          <div id="loading" class="loading" hidden>Searching grounded evidence…</div>
        </div>

        <div id="error" class="panel error" hidden></div>
        <div id="answer" class="panel answer-card" hidden></div>
        <div id="results" class="panel result-card" hidden></div>
        <div id="empty" class="panel empty">
          Ask a question to see the answer, the supporting citations, and the retrieved chunks.
        </div>
      </div>

      <aside class="panel side">
        <div class="note">
          <strong>How this works</strong>
          The server runs SQLite FTS5 for lexical retrieval, a persisted local vector index for semantic retrieval, then fuses both result lists before generating an evidence-backed answer.
        </div>
        <div class="note">
          <strong>What the scores mean</strong>
          `score` is the hybrid fused retrieval score. `confidence` rises when BM25 and vector retrieval both agree on the same chunk.
        </div>
        <div class="note">
          <strong>Oracle corpus</strong>
          Choose the Oracle corpus after building `data/oracle_index`. Citations in that mode point back to the original Oracle URLs.
        </div>
      </aside>
    </section>
  </div>

  <script>
    const questionEl = document.getElementById("question");
    const indexEl = document.getElementById("index-key");
    const topKEl = document.getElementById("top-k");
    const askButton = document.getElementById("ask-button");
    const loadingEl = document.getElementById("loading");
    const errorEl = document.getElementById("error");
    const answerEl = document.getElementById("answer");
    const resultsEl = document.getElementById("results");
    const emptyEl = document.getElementById("empty");

    function escapeHtml(value) {
      return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function setBusy(isBusy) {
      askButton.disabled = isBusy;
      loadingEl.hidden = !isBusy;
    }

    function clearOutput() {
      errorEl.hidden = true;
      answerEl.hidden = true;
      resultsEl.hidden = true;
      emptyEl.hidden = true;
    }

    function renderAnswer(payload) {
      const citations = (payload.citations || []).map(item => `
        <div class="citation">
          <div class="title-row">
            <div class="doc-title">${escapeHtml(item.title)}</div>
            <div class="meta">score ${item.score} · confidence ${item.confidence}</div>
          </div>
          <a href="${item.citation.split(":")[0].startsWith("http") ? item.citation.split(/:(?=\\d+-\\d+$)/)[0] : "#"}" target="_blank" rel="noreferrer">${escapeHtml(item.citation)}</a>
        </div>
      `).join("");

      answerEl.innerHTML = `
        <div class="eyebrow">Answer</div>
        <div class="answer-text">${escapeHtml(payload.answer || "No answer returned.")}</div>
        <div class="citations">${citations || "<div class='meta'>No citations returned.</div>"}</div>
      `;
      answerEl.hidden = false;
    }

    function renderResults(results) {
      const cards = results.map(item => `
        <div class="result">
          <div class="title-row">
            <div class="doc-title">${escapeHtml(item.title)}</div>
            <div class="meta">rank ${item.rank} · score ${item.score} · confidence ${item.confidence}</div>
          </div>
          <div class="meta">${escapeHtml(item.citation)}</div>
          <p>${escapeHtml(item.text)}</p>
        </div>
      `).join("");

      resultsEl.innerHTML = `
        <div class="eyebrow">Evidence</div>
        <div class="results">${cards}</div>
      `;
      resultsEl.hidden = false;
    }

    async function ask() {
      const query = questionEl.value.trim();
      const topK = Number(topKEl.value || "5");
      if (!query) {
        clearOutput();
        emptyEl.hidden = false;
        emptyEl.textContent = "Type a question first.";
        return;
      }

      clearOutput();
      setBusy(true);
      try {
        const response = await fetch("/answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            top_k: topK,
            index_key: indexEl.value
          })
        });
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error || "Request failed.");
        }
        renderAnswer(payload);
        renderResults(payload.evidence || []);
      } catch (error) {
        errorEl.textContent = error.message;
        errorEl.hidden = false;
      } finally {
        setBusy(false);
      }
    }

    askButton.addEventListener("click", ask);
    questionEl.addEventListener("keydown", event => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        ask();
      }
    });

    questionEl.value = "What are Oracle best practices for RMAN with Recovery Appliance?";
  </script>
</body>
</html>
"""


def _json_response(start_response, status: str, payload: dict[str, object]) -> list[bytes]:
    start_response(status, [("Content-Type", "application/json; charset=utf-8")])
    return [json.dumps(payload, indent=2).encode("utf-8")]


def _html_response(start_response, html: str) -> list[bytes]:
    start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
    return [html.encode("utf-8")]


def _read_json_body(environ) -> dict[str, object]:
    length = int(environ.get("CONTENT_LENGTH") or "0")
    raw_body = environ["wsgi.input"].read(length).decode("utf-8")
    return json.loads(raw_body or "{}")


def _resolve_index(body: dict[str, object], environ) -> Path:
    if "index_key" in body:
        return INDEX_OPTIONS.get(str(body["index_key"]), INDEX_OPTIONS["sample"])
    query = parse_qs(environ.get("QUERY_STRING", ""))
    if "index_key" in query:
        return INDEX_OPTIONS.get(query["index_key"][0], INDEX_OPTIONS["sample"])
    return INDEX_OPTIONS["sample"]


def _ensure_index_exists(index_dir: Path) -> None:
    if not (index_dir / "search.db").exists():
        raise FileNotFoundError(f"Index not found at {index_dir}")


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")

    if method == "GET" and path == "/":
        return _html_response(start_response, HTML)

    if method == "GET" and path == "/health":
        return _json_response(start_response, "200 OK", {"status": "ok"})

    if method == "POST" and path in {"/search", "/answer"}:
        try:
            body = _read_json_body(environ)
            query = str(body["query"]).strip()
            top_k = int(body.get("top_k", 5))
            acl_groups = body.get("acl_groups")
            index_dir = _resolve_index(body, environ)
            _ensure_index_exists(index_dir)
            engine = HybridSearchEngine(index_dir)
            if path == "/search":
                payload = {
                    "query": query,
                    "index_dir": str(index_dir),
                    "results": engine.search(query, top_k=top_k, acl_groups=acl_groups),
                }
            else:
                payload = engine.answer(query, top_k=top_k, acl_groups=acl_groups)
                payload["index_dir"] = str(index_dir)
            return _json_response(start_response, "200 OK", payload)
        except Exception as exc:
            return _json_response(start_response, "400 Bad Request", {"error": str(exc)})

    return _json_response(start_response, "404 Not Found", {"error": "not found"})


def main() -> int:
    with make_server("127.0.0.1", 3000, application) as server:
        print("Serving trusted search UI on http://127.0.0.1:3000")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
