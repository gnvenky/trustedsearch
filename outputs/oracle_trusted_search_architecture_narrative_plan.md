# Oracle Trusted Search Architecture Deck

Audience: technical stakeholders, DBAs, architects, and decision makers who want to understand how the local Oracle document Q&A system works.

Objective: explain the application's purpose, architecture, data flow, deployment footprint, and current limits in a way that is presentation-ready.

Narrative arc:
1. establish what the application is and why it exists
2. show the core components and how they connect
3. explain the end-to-end data path from Oracle public sources to grounded answers
4. show what runs locally on the laptop
5. close with strengths and next-step improvements

Slide list:
1. Title slide
2. What the application does
3. System architecture diagram
4. End-to-end processing flow
5. Local deployment and data stores
6. Strengths, limits, and next steps

Source plan:
- local application files:
  - `/Users/venky/Documents/Codex/2026-04-19-build-me-a-trusted-search-using/trusted_search/web_ingest.py`
  - `/Users/venky/Documents/Codex/2026-04-19-build-me-a-trusted-search-using/trusted_search/engine.py`
  - `/Users/venky/Documents/Codex/2026-04-19-build-me-a-trusted-search-using/apps/api/app.py`
  - `/Users/venky/Documents/Codex/2026-04-19-build-me-a-trusted-search-using/data/oracle_public_sources.json`
- previously validated Oracle corpus/index counts from the current workspace

Visual system:
- editorial architecture theme
- warm paper background with dark ink typography
- rust accent for key motion/data paths
- blue accent for runtime/service boundaries
- rounded cards with soft shadows

Imagegen plan:
- none required; deck uses native PowerPoint shapes and editable text

Asset needs:
- native block diagram with arrows
- pipeline flow diagram with numbered stages
- local deployment topology slide with file paths and components

Editability plan:
- all text remains editable PowerPoint text boxes
- all diagrams use native shapes and connectors/arrows
- no rasterized text
