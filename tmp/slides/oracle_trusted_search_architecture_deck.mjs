import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const { Presentation, PresentationFile } = await import("@oai/artifact-tool");

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..", "..");
const OUT_DIR = path.join(ROOT, "outputs");
const SCRATCH_DIR = path.join(ROOT, "tmp", "slides", "oracle_trusted_search_architecture");
const PREVIEW_DIR = path.join(SCRATCH_DIR, "preview");
const PPTX_PATH = path.join(OUT_DIR, "oracle_trusted_search_architecture.pptx");
const W = 1280;
const H = 720;

const BG = "#F6F0E7";
const PANEL = "#FFF9F2";
const INK = "#1E2A33";
const MUTED = "#5E6C77";
const ACCENT = "#BA4B2F";
const ACCENT_SOFT = "#F4D8CF";
const BLUE = "#1F4F64";
const BLUE_SOFT = "#D8E8EF";
const LINE = "#D6CCBE";
const TITLE = "Aptos Display";
const BODY = "Aptos";
const MONO = "Aptos Mono";

async function ensureDirs() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
}

function addShape(slide, geometry, left, top, width, height, { fill = PANEL, line = LINE, lineWidth = 1.2, radius } = {}) {
  const shape = slide.shapes.add({
    geometry,
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: line, width: lineWidth },
  });
  if (radius) shape.radius = radius;
  return shape;
}

function addText(
  slide,
  text,
  left,
  top,
  width,
  height,
  {
    size = 24,
    color = INK,
    bold = false,
    face = BODY,
    align = "left",
    valign = "top",
    fill = null,
    line = null,
  } = {},
) {
  const shape = addShape(slide, "rect", left, top, width, height, {
    fill: fill || "transparent",
    line: line || "transparent",
    lineWidth: 0,
  });
  shape.text = String(text);
  shape.text.fontSize = size;
  shape.text.color = color;
  shape.text.bold = bold;
  shape.text.typeface = face;
  shape.text.alignment = align;
  shape.text.verticalAlignment = valign;
  shape.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  return shape;
}

function addBulletList(slide, items, left, top, width, height, color = INK) {
  const text = items.map((item) => `• ${item}`).join("\n");
  const box = addText(slide, text, left, top, width, height, {
    size: 22,
    color,
    face: BODY,
  });
  box.text.style = "list";
  return box;
}

function addHeader(slide, kicker, title, subtitle) {
  slide.background.fill = BG;
  addShape(slide, "rect", 54, 54, 8, 120, { fill: ACCENT, line: ACCENT, lineWidth: 0 });
  addText(slide, kicker, 82, 58, 420, 26, {
    size: 13,
    color: ACCENT,
    bold: true,
    face: MONO,
  });
  addText(slide, title, 82, 92, 860, 86, {
    size: 34,
    color: INK,
    bold: true,
    face: TITLE,
  });
  if (subtitle) {
    addText(slide, subtitle, 82, 176, 880, 56, {
      size: 18,
      color: MUTED,
      face: BODY,
    });
  }
}

function addFooter(slide, text) {
  addText(slide, text, 82, 684, 1110, 18, {
    size: 10,
    color: MUTED,
    face: MONO,
  });
}

function addCard(slide, title, body, left, top, width, height, accent = ACCENT) {
  addShape(slide, "roundRect", left, top, width, height, {
    fill: PANEL,
    line: LINE,
    lineWidth: 1.2,
  });
  addShape(slide, "rect", left + 18, top + 18, 46, 6, { fill: accent, line: accent, lineWidth: 0 });
  addText(slide, title, left + 18, top + 34, width - 36, 34, {
    size: 21,
    color: INK,
    bold: true,
    face: TITLE,
  });
  addText(slide, body, left + 18, top + 74, width - 36, height - 90, {
    size: 18,
    color: MUTED,
    face: BODY,
  });
}

function addArrow(slide, left, top, width, height, fill = ACCENT_SOFT) {
  addShape(slide, "rightArrow", left, top, width, height, {
    fill,
    line: fill,
    lineWidth: 0,
  });
}

function addMermaidNode(slide, title, left, top, width, height, tone = "accent") {
  const palette = tone === "blue"
    ? { fill: "#F3F9FB", line: BLUE_SOFT, rule: BLUE }
    : { fill: "#FFF5F1", line: ACCENT_SOFT, rule: ACCENT };
  addShape(slide, "roundRect", left, top, width, height, {
    fill: palette.fill,
    line: palette.line,
    lineWidth: 1.2,
  });
  addShape(slide, "rect", left + 14, top + 14, width - 28, 5, {
    fill: palette.rule,
    line: palette.rule,
    lineWidth: 0,
  });
  addText(slide, title, left + 18, top + 28, width - 36, height - 40, {
    size: 18,
    color: INK,
    bold: true,
    face: TITLE,
    align: "center",
    valign: "middle",
  });
}

function buildDeck() {
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  {
    const slide = p.slides.add();
    slide.background.fill = BG;
    addShape(slide, "roundRect", 54, 52, 1172, 616, { fill: "#FFF9F2", line: LINE, lineWidth: 1.2 });
    addShape(slide, "rect", 80, 84, 8, 520, { fill: ACCENT, line: ACCENT, lineWidth: 0 });
    addText(slide, "Oracle Protection Q&A", 110, 92, 420, 24, {
      size: 13,
      color: ACCENT,
      bold: true,
      face: MONO,
    });
    addText(slide, "Trusted Search Architecture", 108, 132, 560, 104, {
      size: 48,
      color: INK,
      bold: true,
      face: TITLE,
    });
    addText(
      slide,
      "A local, grounded application that crawls public Oracle RMAN and ZDLRA content, builds hybrid indexes, and answers questions with cited evidence.",
      110,
      256,
      620,
      120,
      { size: 22, color: MUTED },
    );
    addCard(slide, "Purpose", "Explain how the application acquires Oracle content, stores it locally, retrieves evidence, and produces citation-backed answers in a browser UI.", 108, 418, 446, 156, ACCENT);
    addCard(slide, "Current build", "Public Oracle docs are cached locally, indexed into SQLite FTS plus a persisted vector file, and exposed through a lightweight local web app.", 578, 418, 446, 156, BLUE);
    addShape(slide, "roundRect", 938, 120, 230, 230, { fill: BLUE_SOFT, line: BLUE_SOFT, lineWidth: 0 });
    addText(slide, "92\ndocuments", 938, 154, 230, 94, {
      size: 38,
      color: BLUE,
      bold: true,
      face: TITLE,
      align: "center",
    });
    addText(slide, "1,404 indexed chunks\nbuilt from Oracle public sources", 968, 254, 170, 72, {
      size: 17,
      color: BLUE,
      align: "center",
    });
    addFooter(slide, "Deck generated locally from the current workspace architecture and Oracle index build state.");
  }

  {
    const slide = p.slides.add();
    addHeader(
      slide,
      "APPLICATION OVERVIEW",
      "What the application does",
      "It combines public-source Oracle content, hybrid retrieval, and a local Q&A interface to keep answers inspectable."
    );
    addCard(slide, "1. Acquire sources", "A curated manifest seeds Oracle docs, Recovery Appliance pages, and selected public Oracle sources.", 84, 282, 344, 170, ACCENT);
    addCard(slide, "2. Build local evidence", "Fetched pages are cached as local JSON, then chunked and indexed into a lexical store plus a vector store.", 468, 282, 344, 170, BLUE);
    addCard(slide, "3. Answer with citations", "Questions run through BM25 and vector search, then the UI shows both the answer and the underlying evidence.", 852, 282, 344, 170, ACCENT);
    addArrow(slide, 396, 338, 46, 28);
    addArrow(slide, 780, 338, 46, 28);
    addBulletList(
      slide,
      [
        "Grounded on actual local indexes instead of prompt-only context",
        "Citations point to original Oracle URLs and cached chunk line ranges",
        "Runs entirely on the laptop except during the optional web crawl",
      ],
      96,
      498,
      1040,
      132,
      INK,
    );
    addFooter(slide, "Core application files: web_ingest.py, engine.py, cli.py, app.py, and data/oracle_public_sources.json");
  }

  {
    const slide = p.slides.add();
    addHeader(
      slide,
      "SYSTEM ARCHITECTURE",
      "Architecture diagram",
      "The application is organized as a source layer, indexing layer, retrieval layer, and presentation layer."
    );
    addCard(slide, "Oracle public sources", "docs.oracle.com, Recovery Appliance docs, Oracle MAA pages, curated public sources", 78, 278, 250, 130, ACCENT);
    addCard(slide, "Crawler + parser", "Allowed-domain fetcher in web_ingest.py extracts title, text, and follow-on links", 366, 278, 250, 130, BLUE);
    addCard(slide, "Local corpus cache", "JSON documents in data/oracle_corpus preserve source_uri, text, and metadata", 654, 278, 250, 130, ACCENT);
    addCard(slide, "Index builder", "engine.py chunks content and builds search.db plus vectors.json", 942, 278, 250, 130, BLUE);
    addArrow(slide, 318, 327, 34, 22);
    addArrow(slide, 606, 327, 34, 22);
    addArrow(slide, 894, 327, 34, 22);

    addCard(slide, "SQLite FTS5", "Lexical/BM25-style retrieval over chunk text", 186, 490, 228, 120, BLUE);
    addCard(slide, "Vector index", "Persisted local dense vectors for semantic similarity", 462, 490, 228, 120, ACCENT);
    addCard(slide, "Hybrid search engine", "Runs both searches and merges them with reciprocal-rank fusion", 738, 490, 228, 120, BLUE);
    addCard(slide, "Local web UI + API", "Browser Q&A at / with /search and /answer routes in app.py", 1014, 490, 228, 120, ACCENT);
    addArrow(slide, 414, 538, 30, 22);
    addArrow(slide, 690, 538, 30, 22);
    addArrow(slide, 966, 538, 30, 22);
    addFooter(slide, "Everything after the crawl is local: corpus cache, indexes, retrieval, and the Q&A web interface.");
  }

  {
    const slide = p.slides.add();
    addHeader(
      slide,
      "MERMAID VIEW",
      "Mermaid architecture flow captured in PowerPoint",
      "This slide recreates the Mermaid diagram as editable PowerPoint shapes so it remains presentation-friendly."
    );
    addMermaidNode(slide, "Oracle public sources manifest", 74, 286, 206, 86, "accent");
    addMermaidNode(slide, "Web crawler", 308, 286, 160, 86, "blue");
    addMermaidNode(slide, "Local cached corpus (JSON)", 496, 286, 206, 86, "accent");
    addMermaidNode(slide, "Chunking + metadata extraction", 730, 286, 220, 86, "blue");

    addArrow(slide, 274, 315, 24, 18, BLUE_SOFT);
    addArrow(slide, 462, 315, 24, 18, ACCENT_SOFT);
    addArrow(slide, 696, 315, 24, 18, BLUE_SOFT);

    addMermaidNode(slide, "SQLite FTS5 index", 282, 468, 170, 82, "blue");
    addMermaidNode(slide, "Local vector index\n(vectors.json)", 502, 468, 182, 82, "accent");
    addMermaidNode(slide, "Hybrid retrieval engine", 734, 468, 192, 82, "blue");
    addMermaidNode(slide, "Grounded answer + citations", 974, 468, 214, 82, "accent");

    addArrow(slide, 452, 497, 18, 18, ACCENT_SOFT);
    addArrow(slide, 684, 497, 18, 18, BLUE_SOFT);
    addArrow(slide, 926, 497, 18, 18, ACCENT_SOFT);

    addMermaidNode(slide, "User question", 74, 468, 164, 82, "accent");
    addArrow(slide, 242, 497, 28, 18, ACCENT_SOFT);

    addText(slide, "Equivalent Mermaid logic", 82, 604, 220, 22, {
      size: 13,
      color: ACCENT,
      bold: true,
      face: MONO,
    });
    addText(
      slide,
      "manifest -> crawler -> corpus -> chunking -> {SQLite FTS5 + vector index} -> hybrid retrieval -> grounded answer -> user-facing result",
      82,
      630,
      1120,
      34,
      { size: 15, color: MUTED, face: MONO },
    );
    addFooter(slide, "Mermaid was captured as native editable PowerPoint geometry rather than as a static screenshot.");
  }

  {
    const slide = p.slides.add();
    addHeader(
      slide,
      "PROCESS FLOW",
      "End-to-end data path",
      "A question travels through acquisition, indexing, retrieval, and answer generation before it appears in the browser."
    );
    const y = 320;
    const stages = [
      ["1", "Seed manifest", "Oracle source groups and allowed URL prefixes"],
      ["2", "Fetch and cache", "Crawler stores cleaned pages as local JSON"],
      ["3", "Chunk and index", "SQLite FTS and vectors.json are generated"],
      ["4", "Hybrid retrieve", "BM25 + vector similarity + rank fusion"],
      ["5", "Grounded answer", "Answer text plus citations and evidence cards"],
    ];
    stages.forEach(([num, title, body], idx) => {
      const left = 54 + idx * 244;
      addShape(slide, "roundRect", left, y - 26, 184, 184, {
        fill: idx % 2 === 0 ? PANEL : "#FFF5F1",
        line: idx % 2 === 0 ? LINE : ACCENT_SOFT,
        lineWidth: 1.2,
      });
      addShape(slide, "ellipse", left + 18, y - 6, 44, 44, {
        fill: idx % 2 === 0 ? BLUE_SOFT : ACCENT_SOFT,
        line: "transparent",
        lineWidth: 0,
      });
      addText(slide, num, left + 18, y + 1, 44, 24, {
        size: 21,
        color: idx % 2 === 0 ? BLUE : ACCENT,
        bold: true,
        face: TITLE,
        align: "center",
      });
      addText(slide, title, left + 18, y + 56, 148, 42, {
        size: 20,
        color: INK,
        bold: true,
        face: TITLE,
      });
      addText(slide, body, left + 18, y + 102, 148, 56, {
        size: 16,
        color: MUTED,
      });
      if (idx < stages.length - 1) {
        addArrow(slide, left + 190, y + 50, 34, 20, idx % 2 === 0 ? BLUE_SOFT : ACCENT_SOFT);
      }
    });
    addText(
      slide,
      "Result: the user sees an answer that is constrained by retrieved evidence, plus citations back to the original Oracle content.",
      84,
      592,
      1050,
      44,
      { size: 20, color: BLUE, bold: true, face: TITLE, align: "center" },
    );
    addFooter(slide, "Retrieval confidence increases when both lexical and vector search agree on the same chunk.");
  }

  {
    const slide = p.slides.add();
    addHeader(
      slide,
      "LOCAL DEPLOYMENT",
      "What runs on the laptop",
      "The current build is intentionally simple: one local codebase, one local web server, one lexical index, and one local vector file."
    );
    addShape(slide, "roundRect", 82, 262, 1116, 342, { fill: PANEL, line: LINE, lineWidth: 1.2 });
    addShape(slide, "roundRect", 116, 300, 316, 254, { fill: "#FFF5F1", line: ACCENT_SOFT, lineWidth: 1.2 });
    addShape(slide, "roundRect", 482, 300, 316, 254, { fill: "#F3F9FB", line: BLUE_SOFT, lineWidth: 1.2 });
    addShape(slide, "roundRect", 848, 300, 316, 254, { fill: "#FFF5F1", line: ACCENT_SOFT, lineWidth: 1.2 });
    addText(slide, "Application", 138, 324, 200, 28, { size: 22, bold: true, face: TITLE, color: INK });
    addBulletList(slide, [
      "apps/api/app.py serves the browser UI and JSON endpoints",
      "trusted_search/cli.py provides build, search, answer, and crawl commands",
      "Python process runs the retrieval engine in-process",
    ], 138, 366, 260, 150, INK);
    addText(slide, "Data stores", 504, 324, 200, 28, { size: 22, bold: true, face: TITLE, color: INK });
    addBulletList(slide, [
      "data/oracle_corpus stores cached Oracle pages as JSON",
      "data/oracle_index/search.db stores SQLite FTS5 content",
      "data/oracle_index/vectors.json stores local vector embeddings",
    ], 504, 366, 260, 150, INK);
    addText(slide, "User touchpoints", 870, 324, 220, 28, { size: 22, bold: true, face: TITLE, color: INK });
    addBulletList(slide, [
      "Browser UI at http://127.0.0.1:3000",
      "Q&A response includes answer plus evidence cards",
      "CLI remains available for direct search and debugging",
    ], 870, 366, 260, 150, INK);
    addArrow(slide, 430, 412, 36, 24);
    addArrow(slide, 796, 412, 36, 24);
    addFooter(slide, "No external serving layer or hosted vector database is required in the current architecture.");
  }

  {
    const slide = p.slides.add();
    addHeader(
      slide,
      "ASSESSMENT",
      "Strengths, limits, and next steps",
      "The current application is already useful, but the highest-value improvements are in extraction quality and relevance tuning."
    );
    addCard(slide, "Strengths", "Grounded on actual local indexes\nCitations map to original Oracle URLs\nInteractive browser Q&A\nSimple local deployment footprint", 84, 274, 344, 260, ACCENT);
    addCard(slide, "Current limits", "Oracle pages still carry navigation boilerplate\nBlog ingestion was incomplete on the last crawl\nVector search uses a local file rather than a vector database", 468, 274, 344, 260, BLUE);
    addCard(slide, "Next steps", "Improve page cleaning and chunk filtering\nRepair blog crawling for broader source coverage\nOptionally upgrade the vector layer to Qdrant, pgvector, or FAISS", 852, 274, 344, 260, ACCENT);
    addText(slide, "Recommended near-term path: improve extraction quality first, then upgrade the vector backend if scale or recall demands it.", 126, 580, 1028, 42, {
      size: 21,
      color: BLUE,
      bold: true,
      face: TITLE,
      align: "center",
    });
    addFooter(slide, "This deck describes the application as built locally in the current workspace on April 20, 2026.");
  }

  return p;
}

async function saveBlobToFile(blob, filePath) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  await fs.writeFile(filePath, bytes);
}

async function renderPreviews(presentation) {
  for (let i = 0; i < presentation.slides.items.length; i += 1) {
    const slide = presentation.slides.items[i];
    const preview = await presentation.export({ slide, format: "png", scale: 1 });
    await saveBlobToFile(preview, path.join(PREVIEW_DIR, `slide-${String(i + 1).padStart(2, "0")}.png`));
  }
}

async function main() {
  await ensureDirs();
  const presentation = buildDeck();
  await renderPreviews(presentation);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(PPTX_PATH);
  console.log(PPTX_PATH);
}

await main();
