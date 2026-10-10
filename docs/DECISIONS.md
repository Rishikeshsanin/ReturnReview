# Architecture Decision Log

## ADR-001 — MVP category: cardboard shipping boxes
Chosen for safe staged defects, cheap physical examples, easy multi-angle capture and practical mask annotation.

## ADR-002 — Binary segmentation + separate few-shot recognition
YOLO11n-seg answers **where visible damage is** using one `damage` class. OpenCLIP prototypes answer **what type of damage it resembles**. This prevents a redundant/fake few-shot component.

Target defect labels: `tear`, `crushed_corner`, `dent_or_crush`, plus `unknown` below threshold.

## ADR-003 — Local SQLite first
Supabase is intentionally not connected during early development. It is shared with unrelated projects, so ReturnReview will use SQLite until the shared Project Hub Supabase README/schema is audited read-only and a collision-free namespace is confirmed.

## ADR-004 — One bounded review agent
No multi-agent system, vector DB, MCP or A2A in MVP. Gemini structured generation/tool calling is enough to demonstrate agentic retrieval while preserving reliability.

## ADR-005 — Human authority
AI can recommend `manual_review`, `request_more_evidence`, `no_visible_damage_detected`, `policy_mismatch`, or `insufficient_evidence`. Only the reviewer can approve/reject.

## Current-state note

ADRs 001–005 are preserved as the historical MVP decisions. ADR-002 and
ADR-003 describe earlier implementation stages and are superseded for the
deployed runtime by the decisions below; they remain useful design history.

## ADR-006 — Lightweight production CV runtime

Production uses the checksum-verified `cv-lightweight-1` release:

- MobileNetV3-Small performs cardboard-box category verification.
- Multiclass YOLO11n-seg predicts `tear`, `squeeze`, and `leakage` masks.
- Runtime maps `tear` directly, `leakage` to `unknown`, and `squeeze` to
  `crushed_corner` or `dent_or_crush` using an explicit geometry heuristic.
- OpenCLIP remains part of historical/public-pilot research tooling but is not
  required by the deployed inference path.

This supersedes ADR-002 for the current production implementation without
rewriting the original decision.

## ADR-007 — Dedicated Railway PostgreSQL production persistence

Production persistence uses the dedicated PostgreSQL service in the isolated
ReturnReview Railway project, via private networking and the `public` schema.
The earlier SQLite-first and retained Supabase foundations are historical and
are not the production runtime. This supersedes ADR-003 for production while
preserving it as the record of the early-development choice.
