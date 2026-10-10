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
Polygon-mask only the visible damaged pixels/region. Dataset labels must remain
explicitly tied to the experiment that produced them:

- the original feasibility plan used a binary `damage` class;
- the deployed public-pilot YOLO model is multiclass with native labels
  `tear`, `squeeze`, and `leakage`;
- the project-controlled target taxonomy is `tear`, `crushed_corner`, and
  `dent_or_crush`, with normal images carrying empty labels.

Do not silently mix these schemas. Any conversion must record the source label
and mapping used by the target experiment.

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

The legacy binary validator enforces the original feasibility class map:

```text
0: damage
```

Detection bounding boxes are never accepted as segmentation ground truth.

## Controlled 28-image plan

For the fastest reproducible real pilot, follow `docs/PILOT_ANNOTATION_PLAN.md` and `data/pilot_manifest.csv`.

Validate the manifest before annotation/training:

~~~bash
python scripts/validate_pilot_manifest.py --manifest data/pilot_manifest.csv
~~~

After images are captured, add `--images-dir /path/to/images` to verify that every expected file exists.

## Licensed public segmentation export

A vetted public **instance-segmentation** export can supplement the controlled
pilot. The repository now includes a safe binary-class converter:

~~~bash
python scripts/prepare_public_segmentation.py \
  --input /path/to/yolo-seg-export \
  --output data/dataset/public_damage \
  --include-classes tear,squeeze \
  --source-id roboflow_box_damage_segmentation \
  --source-url https://universe.roboflow.com/tracking-u78ba/box-fsrpn \
  --license "CC BY 4.0"

python scripts/validate_yolo_seg_dataset.py data/dataset/public_damage
~~~

The converter accepts existing polygons only. A detection row such as
`class x_center y_center width height` causes a hard failure rather than being
treated as a mask.

Public data supplements the project-controlled pilot; it does not remove the
need for leakage review or held-out evaluation.

## Current controlled-dataset evidence

The completed synthetic-controlled v1 dataset contains 28 synthetic-generated
images with a fixed box-level split: 12 train, 8 validation, and 8 test. It is
not genuine camera-captured data and its results remain separate from the
licensed public-pilot metrics.

The immutable zero-shot `cv-lightweight-1` test evaluation and the later
train/validation-only adaptation experiment are documented in
`docs/EVALUATION.md` and `docs/FINALIZATION.md`. The adapted checkpoint was not
deployed. Genuine-camera validation remains a separate future requirement.


## Automated public-pilot bootstrap

For the reproducible licensed public-data bootstrap, see `docs/CV_PUBLIC_PILOT.md`.

The automated pilot is deliberately separate from the 28-image project-controlled capture. Public-pilot metrics may be used to validate the engineering pipeline, but they must not be described as metrics from project-controlled data.
