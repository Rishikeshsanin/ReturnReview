# ReturnReview — Viva Revision Sheet

## One-line project explanation

ReturnReview uses computer vision to observe visible package damage, structured policy as factual context, a constrained LLM to draft a grounded review, and a human for the final return decision.

## Why not use only an LLM with images?

Because the academic goal is to make visual evidence measurable and auditable. A dedicated CV pipeline gives segmentation masks, confidence, defect prototypes and held-out metrics. The LLM receives structured evidence rather than inventing its own visual claims.

## Why YOLO segmentation instead of ordinary detection?

Detection gives a box. Segmentation estimates the actual visible damaged region, so we can show an overlay and compute pixel-level IoU/Dice and approximate affected visible-image area.

## Why only one YOLO class: damage?

The model's job is localization: **where is damage?** The few-shot OpenCLIP stage separately answers **what defect does this crop resemble?** This keeps the few-shot component real instead of hiding subtype classification inside YOLO.

## Why OpenCLIP?

It produces semantic image embeddings that can be compared with a small prototype bank. That supports category verification and few-shot recognition without training a large subtype classifier from scratch.

## What is a prototype bank?

For each category/defect, embeddings from labelled reference images are averaged/retained as prototype vectors. A new crop is embedded and compared using cosine similarity.

## Why have an unknown class?

If the best similarity is below threshold, or too close to the second-best class, forcing a known label would be misleading. `unknown` is a safety and calibration feature.

## What is cosine similarity?

For two embedding vectors:

`cos(theta) = (A · B) / (||A|| ||B||)`

Higher similarity means the vectors point in more similar semantic directions.

## Why calibrate thresholds on validation data?

Using the test set to choose thresholds leaks test information and gives optimistic results. Validation tunes the threshold; test measures final generalization.

## Why split by physical box/session?

Multiple photos of the same physical box are highly correlated. Random image splitting could put near-identical views in train and test, causing data leakage.

## IoU vs Dice

IoU:
`intersection / union`

Dice:
`2 × intersection / (predicted + ground truth)`

Both measure mask overlap. Dice usually gives a numerically larger score for the same overlap.

## Precision vs recall for damage masks

Precision asks: of pixels predicted as damage, how many were truly damage?

Recall asks: of true damage pixels, how many did the model find?

## FAR and FRR

For category verification:
- FAR = false acceptance rate: wrong/non-target evidence accepted
- FRR = false rejection rate: valid target evidence rejected

## Why Gemini?

Gemini is used for structured interpretation and policy-grounded drafting, not CV detection. The implementation uses function/tool calls and a response schema.

## What tools can the LLM call?

Read-only tools for:
- case context
- structured visual evidence
- applicable return policy

The backend owns writes and the human owns the final decision.

## What prevents hallucination?

Multiple layers:
1. structured evidence only
2. system prompt boundaries
3. structured response schema
4. evidence-image references
5. deterministic grounding guard
6. human review

## What does the grounding guard check?

It can flag:
- evidence IDs that do not exist
- visual defect claims unsupported by CV
- wrong policy references
- prohibited unsupported causal/intent/fraud claims

## What happens if Gemini fails?

The backend uses a deterministic evidence/policy-based fallback. The app does not need to invent a review or crash.

## Why not multi-agent?

The MVP problem does not require multiple autonomous agents. One bounded workflow is simpler to evaluate, explain and reproduce.

## Who makes the final decision?

The human reviewer. The LLM only recommends review actions such as manual review or requesting more evidence.

## What is stored in Supabase?

ReturnReview has an isolated private `return_review` schema containing cases, image bytes, CV inspection records, findings/overlay bytes, AI reviews, human decisions and audit events.

## Why store image bytes in Postgres?

Railway's local filesystem is ephemeral. Persisting evidence bytes lets the app reconstruct local inference/cache files after container restarts while keeping application data isolated.

## Current limitation before final metrics

A real mask-labelled cardboard damage dataset must be used to train and evaluate the segmentation model. The project deliberately does not report invented CV metrics while that artifact is absent.

## Most important design sentence

> **CV observes. Policy provides facts. LLM interprets. Human decides.**
