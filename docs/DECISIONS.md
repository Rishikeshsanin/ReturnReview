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
