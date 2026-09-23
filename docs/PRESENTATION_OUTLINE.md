# ReturnReview — Final Presentation Structure

Target: **10–12 slides / 7–10 minutes**

## Slide 1 — Title
**ReturnReview**
AI-Powered Product Return Inspection and Evidence-Based Review

Subtitle:
Computer Vision + LLMs + Human-in-the-Loop

## Slide 2 — Problem
Show the return-review problem:
- customer uploads photos
- reviewer must judge visible damage
- policy must be checked
- inconsistent manual interpretation
- generative AI alone can hallucinate evidence

Closing line:
**We separate observation, facts, interpretation and decision.**

## Slide 3 — Core Principle
Large central flow:

~~~text
CV OBSERVES
    ↓
POLICY PROVIDES FACTS
    ↓
LLM INTERPRETS
    ↓
HUMAN DECIDES
~~~

Mention what each layer is *not* allowed to do.

## Slide 4 — Architecture
Use the repository architecture:
Next.js → FastAPI → image validation → OpenCLIP → YOLO segmentation → few-shot prototypes → structured evidence → policy → Gemini → grounding guard → reviewer.

## Slide 5 — Computer Vision Pipeline
Explain:
1. upload validation
2. category verification
3. binary `damage` segmentation
4. damage crop
5. prototype similarity
6. `unknown` threshold
7. multi-view aggregation

Emphasize: **segmentation says where; few-shot says what it resembles.**

## Slide 6 — Why the Design is Academically Strong
- real segmentation instead of fake bounding-box overlays
- held-out physical/session split
- threshold calibration on validation only
- explicit unknown class
- no cross-view 3D claim
- measurable IoU/Dice/F1/FAR/FRR

## Slide 7 — LLM / Agent Workflow
Show the three read-only tools:
- case context
- visual evidence
- return policy

Then:
structured response → deterministic grounding guard → human reviewer.

## Slide 8 — Human-in-the-Loop UI
Use final screenshots:
- case dashboard
- original + overlay evidence
- AI draft review
- reviewer edit/notes
- approve/reject/request more evidence
- audit history

## Slide 9 — Evaluation
Populate only from generated artifacts.

Two-column structure:
**CV**
- IoU / Dice
- precision / recall
- few-shot macro F1
- verification FAR/FRR

**LLM**
- action agreement
- policy correctness
- unsupported claims
- grounding-guard recall
- correction rate
- latency

## Slide 10 — Safety / Failure Behaviour
Demonstrate:
- missing checkpoint → explicit CV unavailable
- low similarity → unknown
- invalid evidence ID → grounding guard flags it
- missing policy → reports missing information
- no model metric → UI says not evaluated

## Slide 11 — Demo Flow
1. create case
2. upload 2–4 images
3. CV inspection
4. overlay + defect evidence
5. grounded review
6. human correction/decision
7. audit trail
8. evaluation dashboard

## Slide 12 — Conclusion
Three points:
- evidence-first, not hallucination-first
- measurable CV + constrained LLM
- human retains decision authority

End with:
**ReturnReview turns AI into an auditable reviewer assistant, not an autonomous claims judge.**
