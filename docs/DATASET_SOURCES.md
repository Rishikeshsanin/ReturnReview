# Candidate Public Dataset Sources

ReturnReview may use public datasets to bootstrap **research/training**, but dataset provenance and task suitability are part of the evaluation protocol.

The canonical machine-readable source list is `data/dataset_sources.json`.

## Verified candidates — 2026-09-23

### 1. Roboflow — box instance segmentation
- URL: https://universe.roboflow.com/test-cardboard/box-fsrpn-4kgfi
- Published task: instance segmentation
- License shown by source: CC BY 4.0
- Classes shown by source: `leakage`, `squeeze`, `tear`

Potential use:
- candidate pixel polygons for the binary `damage` segmentation task **after visual quality review**
- direct few-shot subtype support only for `tear`

Do **not** automatically map `squeeze` to `dent_or_crush`; that needs manual review. `leakage` is outside the locked subtype taxonomy.

### 2. Roboflow — Cardboard Damage V2
- URL: https://universe.roboflow.com/revas-workspace-e6qol/cardboard-damage-v2
- Published task: object detection
- License shown by source: CC BY 4.0
- Damage labels include scratch/dent/hole/tear

Potential use:
- candidate damage crops and prototype/reference imagery
- extra category-verification material

Bounding boxes are **not** segmentation masks and must never be used as pixel-mask ground truth.

### 3. Roboflow — cardboard boxes
- URL: https://universe.roboflow.com/inft2060-ffjce/cardboard-boxes-4h3rr
- Published task: object detection
- License shown by source: CC BY 4.0
- Classes: `Box`, `Damaged Box`

Potential use:
- candidate box/damaged-box reference imagery
- category verification

It is not subtype-labelled mask ground truth.

## Import rule

Before importing any export:

1. Re-open the source and re-check the license/version.
2. Record source ID + source URL + export date.
3. Keep raw data out of Git by default.
4. Run `audit_pilot_images.py`.
5. For YOLO segmentation exports, run `validate_yolo_seg_dataset.py`.
6. Manually inspect a sample of masks before training.
7. Split by physical item/session/source cluster where identity information is available.
8. Tune thresholds on validation only.
9. Keep test data untouched until final evaluation.

If a source's license, provenance, or mask semantics are ambiguous, exclude it rather than silently assuming.
