# Pilot Dataset Protocol

## Category
Cardboard / corrugated shipping boxes.

## Defects
- tear
- crushed_corner
- dent_or_crush
- normal/no visible damage examples

## First pilot requested
Start with **20–30 images** from at least **5 physical box states/items** before collecting the full dataset.

For each state capture 3–5 views, mixing front/back/side/top as appropriate. Use at least two backgrounds and two lighting conditions. Keep the physical item/session ID in filenames.

Example: `box03_crushedcorner_session1_front_01.jpg`.

## Annotation
Polygon-mask only the visible damaged pixels/region. The segmentation dataset uses a single class: `damage`.

## Leakage rule
Do not put near-identical images of the same physical box/session into both training and test. Split by physical item/session.

## Target after feasibility
Roughly 150–400 good images if needed; quality is more important than raw count.


## Public-source bootstrap

Public/licensed images can supplement the real pilot, but they do not remove the need to inspect mask semantics and leakage.

See `docs/DATASET_SOURCES.md` for the vetted candidate list.

For a YOLO segmentation export:

```bash
python scripts/validate_yolo_seg_dataset.py /path/to/dataset
```

The validator enforces the locked training class map:

```text
0: damage
```

Detection bounding boxes are never accepted as segmentation ground truth.
