# ReturnReview

**ReturnReview: An AI-Powered Product Return Inspection and Evidence-Based Review System Using Computer Vision and Large Language Models**

ReturnReview is an evidence-first semester project for **Fundamentals of Computer Vision** and **Working with Large Language Models**. Computer vision localizes visible damage; policy retrieval supplies factual rules; an LLM prepares a grounded review; a human reviewer makes the final decision.

## Live deployment

- Web UI: `https://returnreview-web-production.up.railway.app`
- API: `https://returnreview-api-production.up.railway.app`
- API health: `https://returnreview-api-production.up.railway.app/health`

Both services are isolated inside the dedicated Railway **ReturnReview** project. The backend uses a ReturnReview-only persistent volume mounted at `/data`.

> **Current AI status:** the hosted product shell is live, but project-specific CV inference and Gemini are intentionally disabled until the real pilot dataset/checkpoint/prototype bank and Gemini API key are available. The API refuses to fabricate CV evidence.

## MVP scope

- One category: **cardboard shipping boxes**
- Visible external defects: `tear`, `crushed_corner`, `dent_or_crush`, `unknown`
- Multi-angle JPEG/PNG/WebP uploads
- Real binary damage segmentation using a fine-tuned YOLO segmentation checkpoint
- OpenCLIP category verification and prototype-based few-shot defect recognition
- Conservative multi-view evidence aggregation
- Structured evidence + policy retrieval
- Gemini tool-calling review agent with deterministic fallback + grounding guard
- Human approve/reject/request-more-evidence
- Reviewer edits, notes and audit history
- Real evaluation pipelines; no fabricated metrics

## Core principle

> **CV observes. Policy provides facts. LLM interprets. Human decides.**

## Repository

```text
ReturnReview/
├── frontend/                 # Next.js + TypeScript
├── backend/                  # FastAPI + SQLAlchemy
├── data/                     # structured policies
├── scripts/                  # training, calibration and evaluation
├── docs/                     # architecture, API, model, security, demo
├── Dockerfile                # backend production container
└── .env.example
```

## Current development status

Implemented and tested:
- case creation/history/detail
- validated 2–4 image upload flow
- persistent hosted SQLite + file storage
- YOLO segmentation adapter
- OpenCLIP category verification + few-shot adapter
- segmentation-overlay generation
- structured visual evidence + multi-view aggregation
- bounded Gemini tool workflow + deterministic fallback
- deterministic unsupported-claim grounding guard
- policy retrieval
- human review/edit/decision flow
- audit timeline and request tracing
- real IoU/Dice/F1/FAR/FRR/review-evaluation scripts
- backend + frontend production containers
- CI for backend tests, frontend build and both container healthchecks
- live Railway frontend/backend deployment

**The next hard dependency is real pilot imagery.**

See [`docs/CHECKLIST.md`](docs/CHECKLIST.md).

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

For actual CV training/inference:

```bash
pip install -r requirements-cv.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `.env` where appropriate. Never commit secrets.

## CV workflow

```text
image validation
  -> OpenCLIP category verification
  -> YOLO11n-seg binary damage localization
  -> damage-crop embeddings
  -> few-shot prototype matching
  -> conservative multi-view aggregation
  -> structured evidence
```

The CV path does **not** use Gemini for visual detection.

## LLM workflow

The review agent can read trusted case context, stored CV evidence and the applicable policy. It cannot approve/reject a return, write arbitrary data, infer fraud/intent/causality or invent visual findings. A deterministic grounding guard validates the generated draft before it reaches the reviewer.

## Data safety

The shared Supabase **Projects Hub** was inspected **read-only**. ReturnReview did not create or modify any Hub schema/table/bucket/data. The repository now contains the required `AGENTS.md` and `SUPABASE_HUB_RULES.md` safety contracts for any future integration.

Hosted persistence currently stays isolated on a dedicated Railway volume instead of using shared Supabase.

## Limitations

- one product category initially
- external visible damage only
- CV checkpoint still requires project-specific labelled data
- image quality affects confidence
- unseen/ambiguous defects remain `unknown`
- no internal-damage, fraud, intent, authenticity or causal-responsibility inference
- human reviewer owns the final decision

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Architecture decisions](docs/DECISIONS.md)
- [API](docs/API.md)
- [Dataset protocol](docs/DATASET.md)
- [Evaluation](docs/EVALUATION.md)
- [Model card](docs/MODEL_CARD.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Demo runbook](docs/DEMO.md)
- [Development checklist](docs/CHECKLIST.md)
