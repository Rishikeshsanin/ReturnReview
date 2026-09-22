# ReturnReview Data Workspace

Raw pilot photos and final training data are intentionally **not committed** to the public repository by default.

## Pilot photo naming

Recommended format:

```text
box03_crushedcorner_session1_front_01.jpg
box03_crushedcorner_session1_left_02.jpg
box04_tear_session1_front_01.jpg
box05_normal_session1_top_01.jpg
```

Allowed pilot labels:

- `normal`
- `tear`
- `crushedcorner` / `crushed_corner`
- `dentcrush` / `dent_or_crush`

The physical/session grouping is derived from `boxNN + sessionNN`. Images from one such group must never be divided across train/validation/test.

## Before annotation

Run:

```bash
python scripts/audit_pilot_images.py /path/to/raw_photos
python scripts/split_by_session.py --audit artifacts/pilot_audit.json
```

The first script flags unreadable, low-resolution, blurry, unusually dark/bright, exact-duplicate and near-duplicate photos. These are warnings for human review, not automatic rejection.

The second script creates a deterministic split manifest grouped by physical item/session to reduce data leakage.

## Annotation

After the pilot is accepted, annotate visible damaged regions as a **single segmentation class: `damage`**. Normal images have no damage polygon.

The few-shot defect label is maintained separately from the segmentation class.
