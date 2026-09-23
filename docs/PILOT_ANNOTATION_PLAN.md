# 28-Image Pilot Capture and Annotation Plan

This plan turns the remaining dataset work into one small, controlled pilot.

## Goal

Capture **28 real images** from **7 physical box states/items**, 4 views each.

This is enough for a first feasibility experiment. It is **not automatically the final training dataset**.

## Physical box states

| Item/session | Visible state | Images |
|---|---|---:|
| normal01 | normal / no visible damage | 4 |
| tear01 | tear | 4 |
| tear02 | tear | 4 |
| crushed01 | crushed corner | 4 |
| crushed02 | crushed corner | 4 |
| dent01 | dent/crush | 4 |
| dent02 | dent/crush | 4 |

Total: **28 images**

## Views per item

Capture:
- front
- left
- right
- top

If a view cannot show the defect, still keep it. Negative views from a damaged physical item are useful and make the task more realistic.

## Capture diversity

Across the 7 items/sessions:
- use at least 2 backgrounds
- use at least 2 lighting conditions
- vary distance slightly
- avoid motion blur
- keep the box large enough to inspect
- do not use filters/beauty enhancement
- keep original resolution where possible

## File naming

Use:

`<item_id>_<defect>_<view>_<index>.jpg`

Examples:
- `tear01_tear_front_01.jpg`
- `crushed02_crushed_corner_left_01.jpg`
- `normal01_normal_top_01.jpg`

## Annotation

For the YOLO segmentation dataset:
- class map is exactly `0: damage`
- draw polygon masks around **visible damaged pixels/region only**
- do not outline the entire cardboard box
- normal images have no damage polygon
- do not convert a bounding rectangle into a fake polygon mask
- do not annotate imagined internal damage

Recommended annotation tools:
- CVAT
- Roboflow Annotate
- Label Studio

Export to YOLO segmentation format and run:

~~~bash
python scripts/validate_yolo_seg_dataset.py /path/to/export
~~~

## Few-shot subtype references

Keep the subtype label in the manifest:
- `tear`
- `crushed_corner`
- `dent_or_crush`
- `normal`

The segmentation model still trains on one binary `damage` class. The subtype labels are for prototype/reference construction and evaluation.

## Leakage rule

The same physical item/session must never appear across train and test.

Only expand to 150–400 images if the pilot shows the pipeline is feasible and failure modes are understood.
