# ReturnReview

**ReturnReview: An AI-Powered Product Return Inspection and Evidence-Based Review System Using Computer Vision and Large Language Models**

ReturnReview is an evidence-first semester project for **Fundamentals of Computer Vision** and **Working with Large Language Models**. Computer vision localizes visible damage; policy retrieval supplies factual rules; an LLM prepares a grounded review; a human reviewer makes the final decision.

## MVP scope

- One category: **cardboard shipping boxes**
- Visible external defects: `tear`, `crushed_corner`, `dent_or_crush`, `unknown`
- Multi-angle JPEG/PNG/WebP uploads
- Real binary damage segmentation using a fine-tuned YOLO segmentation checkpoint
- OpenCLIP category verification and few-shot defect prototype matching
- Structured evidence + policy retrieval
- Gemini tool-calling review agent with deterministic fallback
- Human approve/reject/request-more-evidence
- Audit/history-ready persistence
- Real evaluation artifact endpoint (never fabricated)

## Core principle

> **CV observes. Policy provides facts. LLM interprets. Human decides.**

## Repository

```text
ReturnReview/
├── frontend/                 # Next.js + TypeScript
├── backend/                  # FastAPI + SQLAlchemy
├── data/                     # policies + future dataset metadata
├── scripts/                  # training/evaluation/prototype tools
├── docs/                     # architecture, ADRs, dataset protocol
└── .env.example
```

## Current development status

The application foundation, case workflow, upload validation, local persistence, policy lookup, structured review, human-decision flow, audit events, CV adapter, prototype tooling and training/evaluation entry points are implemented. **The app intentionally refuses to present a real CV result until a trained checkpoint and prototype bank exist.** Pilot image collection/annotation is the next hard dependency.

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

Backend health: `http://localhost:8000/health`  
OpenAPI: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

### Environment

Copy `.env.example` to `.env`. Never commit secrets.

Gemini remains disabled until these are set server-side:

```text
RETURNREVIEW_GEMINI_API_KEY=...
RETURNREVIEW_GEMINI_MODEL=gemini-3.8-flash
RETURNREVIEW_LLM_ENABLED=true
```

## CV workflow

```text
image validation
  -> OpenCLIP category prototype verification
  -> YOLO11n-seg binary damage localization
  -> damage crop embeddings
  -> few-shot prototype matching
  -> structured evidence
```

The CV path is intentionally project-specific. It does not call Gemini for damage detection.

## LLM workflow

The Gemini agent has only read tools for trusted case context, stored visual evidence and the relevant policy. Database writes and the final reviewer decision remain deterministic backend actions.

## Data safety

ReturnReview currently uses **local SQLite and local file storage**. It does **not** connect to Supabase yet. Because Supabase is shared with unrelated applications, no schema/table/bucket change will be made until the Project Hub Supabase README and current shared schema are inspected read-only and a safe namespace is established.

## Limitations

- One product category initially
- External visible damage only
- Segmentation requires project-specific labelled data
- Image quality affects confidence
- Unseen/ambiguous defects remain `unknown`
- Internal damage, fraud, intent, authenticity and causal responsibility are not inferred
- Human reviewer owns the final decision

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Pilot dataset protocol](docs/DATASET.md)
- [Development checklist](docs/CHECKLIST.md)
