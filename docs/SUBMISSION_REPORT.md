# ReturnReview — Final Academic Report Draft

## Title

**ReturnReview: An AI-Powered Product Return Inspection and Evidence-Based Review System Using Computer Vision and Large Language Models**

## Abstract

Product-return inspection is often inconsistent because reviewers must combine visual evidence, customer claims and policy rules under time pressure. ReturnReview is an evidence-first academic prototype that separates those responsibilities into independently testable components. Computer vision verifies the product category, localizes visible external damage and assigns a conservative few-shot defect label. A structured policy layer supplies return rules. A bounded large-language-model workflow converts the structured evidence and policy into a draft review, while a deterministic grounding guard blocks unsupported claims. A human reviewer remains responsible for the final decision.

The MVP focuses on corrugated/cardboard shipping boxes and the visible defect taxonomy `tear`, `crushed_corner`, `dent_or_crush`, and `unknown`. The implementation uses FastAPI, SQLAlchemy, Next.js, YOLO11 segmentation, OpenCLIP prototype matching, structured policy retrieval and Gemini tool calling. The project deliberately refuses to fabricate CV findings or evaluation metrics when a trained checkpoint or validated data are unavailable.

> Final numerical results must be inserted only from the repository's generated held-out evaluation artifacts.

## 1. Problem Statement

A return reviewer needs to answer several different questions:

1. Is the submitted evidence actually showing the expected product category?
2. Is visible external damage present, and where?
3. What known defect class does that region most closely resemble?
4. Which return-policy clause applies?
5. Is the available evidence sufficient for a human decision?

A single unconstrained generative model is a poor fit for all five questions because it can blur observation, policy and inference. ReturnReview therefore follows:

> **CV observes. Policy provides facts. LLM interprets. Human decides.**

## 2. Objectives

- Build a reproducible visible-damage inspection pipeline.
- Localize damage at pixel/region level rather than only classifying an entire image.
- Support a few-shot defect taxonomy without pretending an unseen defect is known.
- Aggregate multi-angle evidence conservatively.
- Ground generated review text in machine-readable evidence and policy.
- Keep the final approve/reject action human-owned.
- Produce measurable CV and LLM evaluation artifacts.
- Keep the hosted application deployable, auditable and safe.

## 3. Scope

### Included
- one product category: cardboard/corrugated shipping boxes
- 2–4 evidence images per case
- JPEG/PNG/WebP validation
- category verification
- visible external damage segmentation
- few-shot defect recognition
- policy retrieval
- grounded draft review
- human approve/reject/request-more-evidence
- reviewer edits and notes
- audit timeline

### Explicitly excluded
- internal/non-visible damage
- fraud or intent inference
- authenticity claims
- causal-responsibility claims
- fully autonomous final decisions
- unsupported visual descriptions

## 4. System Architecture

~~~text
Next.js reviewer UI
        |
        v
FastAPI REST backend
        |
        +--> image validation / normalization
        |
        +--> OpenCLIP category verification
        |
        +--> YOLO11n-seg binary damage localization
        |
        +--> OpenCLIP few-shot defect prototypes
        |
        +--> conservative multi-view aggregation
        |
        +--> structured visual evidence
        |
        +--> structured return policy
        |
        +--> bounded Gemini tool workflow
        |
        +--> deterministic grounding guard
        |
        +--> human reviewer decision / audit
~~~

Hosted runtime:
- ReturnReview web: Railway
- ReturnReview API: Railway
- durable persistence foundation: isolated `return_review` schema in the shared Supabase Project Hub

## 5. Computer Vision Design

### 5.1 Image validation

Every upload is validated for:
- MIME/type
- file size
- corruption
- orientation
- minimum dimensions
- obvious blur/darkness warnings

This separates poor evidence quality from model confidence.

### 5.2 Category verification

An OpenCLIP ViT-B/32 embedding is compared with a cardboard-box prototype. A threshold calibrated only on validation data determines whether the category is accepted.

### 5.3 Damage segmentation

YOLO11n-seg is fine-tuned with a **single `damage` class**.

The segmentation model answers only:

> Where is visible damage?

It does not duplicate the defect-subtype classifier.

### 5.4 Few-shot defect recognition

Each localized damage crop is embedded with OpenCLIP and compared with labelled prototype embeddings:

- `tear`
- `crushed_corner`
- `dent_or_crush`

If similarity is too low, or the best-vs-second-best margin is too small, the result becomes:

- `unknown`

This prevents forced classification.

### 5.5 Multi-view aggregation

Findings are grouped conservatively by predicted defect type and supporting image IDs. ReturnReview does not claim to reconstruct a 3D object or identify the exact same physical defect across views.

## 6. LLM Design

Gemini is used only after structured CV evidence and policy have been produced.

The bounded tool workflow exposes read-only functions for:
- trusted case context
- structured visual evidence
- applicable return policy

The model must return a structured review schema containing:
- case summary
- evidence-linked visual findings
- policy reference
- review status
- recommended human-review action
- missing information
- uncertainties
- unsupported-claim flag

The LLM cannot directly approve or reject a return.

## 7. Grounding Guard

A deterministic validator checks generated output before it reaches the reviewer.

Examples of guarded failures:
- non-existent evidence-image IDs
- defect claims not present in CV evidence
- unsupported policy references
- prohibited causality, intent or fraud claims

When a violation is detected, the review is flagged and forced toward human/manual review.

## 8. Persistence and Audit

The application has a local SQLite recovery/development path and an isolated Supabase Postgres production design.

ReturnReview owns only:
- schema `return_review`
- seven ReturnReview tables
- dedicated `return_review_backend` role

Evidence images and generated overlay bytes can be persisted directly in the database so Railway local disk is only a temporary inference/cache layer.

Every meaningful workflow action is recorded in the audit timeline.

## 9. Evaluation Protocol

### 9.1 Segmentation
Report from held-out physical/session-separated samples:
- mean pixel IoU
- mean Dice
- damaged-image IoU/Dice
- pixel precision
- pixel recall
- optional YOLO mask mAP
- latency

### 9.2 Few-shot recognition
Report:
- accuracy
- macro F1
- per-class precision/recall/F1
- confusion matrix

### 9.3 Product verification
Report:
- verification accuracy
- false acceptance rate
- false rejection rate
- calibrated threshold

### 9.4 LLM review
Using the fixed manually reviewed evaluation set, report:
- action agreement
- policy correctness
- unsupported-claim rate
- grounding-guard recall
- human correction rate
- average LLM latency

## 10. Results

**Do not manually type guessed values here.**

Insert values only from:
- `artifacts/evaluation/metrics.json`
- `artifacts/evaluation/llm_metrics.json`

Recommended final table:

| Component | Metric | Held-out result |
|---|---|---:|
| Segmentation | Pixel IoU | TBD from artifact |
| Segmentation | Dice | TBD from artifact |
| Segmentation | Precision | TBD from artifact |
| Segmentation | Recall | TBD from artifact |
| Few-shot | Accuracy | TBD from artifact |
| Few-shot | Macro F1 | TBD from artifact |
| Verification | Accuracy | TBD from artifact |
| Verification | FAR | TBD from artifact |
| Verification | FRR | TBD from artifact |
| LLM | Action agreement | TBD from artifact |
| LLM | Policy correctness | TBD from artifact |
| LLM | Unsupported-claim rate | TBD from artifact |
| LLM | Human correction rate | TBD from artifact |
| LLM | Avg latency | TBD from artifact |

## 11. Safety and Limitations

- The project handles visible external evidence only.
- Image quality and dataset coverage directly affect performance.
- Few-shot recognition may return `unknown`.
- The system does not infer fraud, intent, authenticity or responsibility.
- Policy is factual input, not generated knowledge.
- The final decision remains human-owned.
- The deployed API refuses CV inference when validated model artifacts are absent.
- Evaluation pages refuse to invent metrics.

## 12. Engineering Quality

The repository includes:
- backend tests
- frontend production build checks
- backend/frontend container smoke tests
- Railway governance CI
- dataset validation scripts
- fixed LLM evaluation-set validation
- readiness reporting
- model/security/evaluation/deployment documentation

## 13. Conclusion

ReturnReview demonstrates a modular alternative to a monolithic "AI decides everything" return system. By separating observation, policy, interpretation and decision authority, each layer can be evaluated independently and failure can be surfaced explicitly.

The final academic result should be judged on real held-out CV performance, grounded LLM behaviour, human-correction behaviour and the ability to explain uncertainty—not on fabricated confidence or autonomous-looking demos.
