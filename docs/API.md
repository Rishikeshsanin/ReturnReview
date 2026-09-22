# API Reference

Base URL in development: `http://localhost:8000`

Interactive OpenAPI documentation is available at `/docs`.

## Health
- `GET /health` — environment, LLM availability and configured CV model version.

## Cases
- `POST /api/cases` — create one cardboard-box return case.
- `GET /api/cases` — list cases.
- `GET /api/cases/{case_id}` — case, images, structured CV evidence, latest AI review, human decision and audit timeline.
- `POST /api/cases/{case_id}/images` — multipart image + view label. JPEG/PNG/WebP only; 2–4 views for inspection.
- `POST /api/cases/{case_id}/inspect` — real CV pipeline. Returns 503 if the trained checkpoint/prototype bank is unavailable; it never fabricates evidence.
- `POST /api/cases/{case_id}/ai-review` — bounded evidence/policy review workflow.
- `POST /api/cases/{case_id}/decision` — human APPROVE / REJECT / REQUEST_MORE_EVIDENCE, optional notes and edited review JSON.

## Policies
- `GET /api/policies` — structured policy records used by the agent.

## Metrics
- `GET /api/metrics` — real persisted evaluation artifacts only. Before evaluation, returns `not_evaluated`.

## Error model
Expected validation/workflow errors use normal HTTP 4xx/503 responses with a concise `detail`. Unexpected exceptions are logged server-side and exposed only as a generic 500 response plus request ID.
