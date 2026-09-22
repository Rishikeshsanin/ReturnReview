# ReturnReview Architecture

## Evidence boundary

ReturnReview deliberately separates perception from reasoning:

1. **Computer vision observes** visible evidence.
2. **Evidence records** store model version, confidence and regions.
3. **Policy service provides facts** from structured policy records.
4. **LLM interprets** only the evidence + case metadata + policy.
5. **Human reviewer decides** approve/reject/request-more-evidence.

## Runtime architecture

```mermaid
flowchart TD
  UI[Next.js UI] --> API[FastAPI]
  API --> CASES[(Case DB)]
  API --> STORE[Image storage]
  API --> CV[CV service]
  CV --> SEG[YOLO11n-seg: damage mask]
  CV --> FEW[OpenCLIP: few-shot defect label]
  CV --> EV[Structured evidence]
  API --> POL[Structured policy lookup]
  EV --> AG[Review service]
  POL --> AG
  AG --> GEM[Gemini 3.8 Flash]
  AG --> REV[Structured review]
  REV --> UI
  UI --> HUMAN[Human reviewer]
  HUMAN --> API
  API --> AUDIT[(Audit history)]
```

## Safety design

- No final operational decision is delegated to the LLM.
- LLM receives structured evidence, not authority to invent image findings.
- Database writes are deterministic backend actions, not autonomous model tools.
- CV inference refuses to claim success if no trained checkpoint exists.
- Evaluation UI reads persisted metric artifacts and never fabricates numbers.
