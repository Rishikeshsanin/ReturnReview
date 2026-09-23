# ReturnReview Model Card

## Intended use
Academic MVP for external visible damage inspection of cardboard shipping boxes. The system assists a human reviewer and is not a final decision authority.

## Computer vision pipeline
1. OpenCLIP ViT-B/32 embedding similarity for category verification.
2. Fine-tuned YOLO11n-seg model with a single `damage` segmentation class.
3. OpenCLIP prototype matching on localized damage crops for few-shot labels:
   - tear
   - crushed_corner
   - dent_or_crush
   - unknown below confidence/margin thresholds

## Why one segmentation class?
Localization answers *where is visibly damaged?*. Prototype matching separately answers *what defect does the region resemble?*. This keeps few-shot recognition genuine rather than duplicating a multi-class detector.

## Training status
**No project-specific trained checkpoint is published yet.** Training begins after the pilot dataset is captured and annotated. Until then, the API deliberately returns CV-unavailable instead of simulated damage findings.

## Required evaluation
- pixel IoU / Dice
- pixel precision / recall
- YOLO mask mAP as secondary metric
- few-shot accuracy / macro F1 / per-class F1
- category verification accuracy and threshold calibration
- inference latency

## Known limitations
- one category
- visible external damage only
- performance depends on capture conditions and dataset coverage
- prototype matching can return unknown
- no inference about internal damage, causality, responsibility, fraud or authenticity

## Prototype-bank folder contract

`scripts/build_prototypes.py` requires these exact reference folders:

~~~text
reference_images/
├── category_cardboard_box/
├── defect_tear/
├── defect_crushed_corner/
└── defect_dent_or_crush/
~~~

`unknown` intentionally has no prototype. It is produced when similarity or
the top-vs-second-best margin falls below the calibrated thresholds.

Reference/prototype images must come from training/reference material only, not
the held-out test set.
