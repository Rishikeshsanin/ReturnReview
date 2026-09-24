# Public CV Pilot Pipeline

ReturnReview keeps two data tracks separate:

1. **Project-controlled pilot** — the 28-image capture plan in `PILOT_ANNOTATION_PLAN.md`. This remains the preferred final academic evidence because the capture conditions and physical-box identities are controlled by the project.
2. **Licensed public pilot** — a reproducible bootstrap experiment used to train and validate the engineering pipeline before project-controlled images are available.

The public pilot must never be presented as if the 28 project-controlled images were captured.

## Pinned public segmentation source

The automated workflow uses the Roboflow Universe project:

- project: `tracking-u78ba/box-fsrpn`
- pinned version: `16`
- published task: instance segmentation
- published license recorded by ReturnReview: CC BY 4.0
- source classes used for binary damage segmentation: `tear`, `squeeze`
- source class excluded from binary damage training: `leakage`

Existing source polygons are remapped to the single ReturnReview segmentation class `damage`. Detection boxes are never converted into fake masks.

## Subtype evaluation mapping

The public source does not perfectly match ReturnReview's locked subtype taxonomy.

For the public-pilot semantic-classification evaluation only:

- `tear` -> `tear` (direct match)
- `squeeze` -> `dent_or_crush` (explicit compression-damage proxy)
- `leakage` -> `unknown` (out-of-taxonomy rejection example)
- `crushed_corner` -> **not scored** because the source has no direct held-out label

This limitation is carried into the generated metrics artifact.

## Semantic prototype bank

The public pilot builds OpenCLIP **text-derived semantic prototypes** for:

- cardboard shipping box
- tear
- crushed corner
- dent or crush

These are not described as project-controlled few-shot image prototypes. The category, defect-similarity, and ambiguity-margin thresholds are calibrated on validation data and then evaluated once on held-out test data.

## Training workflow

Workflow:

`.github/workflows/train_cv_public_pilot.yml`

It:

1. downloads the pinned public instance-segmentation export using a private `ROBOFLOW_API_KEY` GitHub Actions secret;
2. validates/remaps only genuine polygon annotations;
3. creates a deterministic CPU-sized pilot without moving examples across source splits;
4. trains YOLO11n-seg;
5. reports held-out pixel IoU/Dice/precision/recall and YOLO mask mAP;
6. builds/calibrates/evaluates the OpenCLIP semantic prototype path;
7. packages the exact checkpoint, prototype bank, thresholds, provenance, and metrics;
8. publishes the result as a GitHub **prerelease candidate**, not as a final model.

The workflow does not store the Roboflow API key in logs or repository files.

## Production gate

A public-pilot candidate is not automatically deployed. Before production activation, inspect:

- dataset validator status
- held-out segmentation metrics
- category verification FAR/FRR
- semantic defect metrics and class coverage
- generated release manifest/checksums
- runtime size and latency

If the candidate is technically useful, it may power a clearly labelled public-pilot demo while the 28-image controlled capture remains a separate final-evidence task.
