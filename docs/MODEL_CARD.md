# ReturnReview Model Card

## Intended use
Academic MVP for external visible damage inspection of cardboard shipping boxes. The system assists a human reviewer and is not a final decision authority.

## Current production CV pipeline
1. **MobileNetV3-Small** binary cardboard-box verification.
2. **YOLO11n-seg** multiclass visible-damage segmentation/localization.
3. Runtime source-class mapping:
   - `tear` → `tear`
   - `squeeze` → `dent_or_crush` or `crushed_corner` via explicit corner-geometry heuristic
   - `leakage` → `unknown`
4. Conservative multi-view aggregation into structured evidence.

The production runtime does **not** require OpenCLIP.

## Production release
Current release: `cv-lightweight-1`.

The release is a checksum-verified public-data engineering candidate. It is deployed only as an assistive CV component inside a human-in-the-loop workflow.

## Public-pilot evaluation
Held-out licensed public-data results:
- category verification: 100% accuracy/F1 on 32 held-out images (16 positives / 16 disjoint generic negatives)
- segmentation mean IoU: 14.1%
- segmentation mean Dice: 20.0%
- mask mAP@50: 12.9%
- combined CPU inference: ~185.6 ms/image on GitHub-hosted Ubuntu CPU
- measured CV peak RSS: ~802.7 MB
- estimated API + CV footprint: ~894.7 MB; recorded 1 GB capacity gate passes with 64 MB reserve

These segmentation results are modest and are not presented as production-grade accuracy.

## Synthetic-controlled stress test
A separate 28-image **synthetic-generated controlled v1** dataset was used to stress-test domain transfer. It is not genuine camera-captured or real-world validation.

Existing production candidate on fixed 8-image test split:
- all-image IoU: 0.042566
- all-image Dice: 0.075557
- damaged-only IoU: 0.056754
- damaged-only Dice: 0.100743
- micro precision: 0.077948
- micro recall: 0.724991
- mask mAP@50: 0.000000
- no predicted mask: 3/8
- false-positive masks on normal images: 2/2

MobileNetV3 accepted all 28 positive cardboard-box images. This gives 100% positive recall only; the synthetic-controlled set has no non-box negatives, so specificity/FAR cannot be measured from it.

## Controlled adaptation experiment
A single train/validation-only transfer-learning experiment was run on the synthetic-controlled set. The fixed test boxes were excluded from training and checkpoint selection and evaluated once afterward.

Adapted test results:
- all-image IoU: 0.280624
- all-image Dice: 0.299196
- damaged-only IoU: 0.040832
- damaged-only Dice: 0.065594
- micro precision: 0.246630
- micro recall: 0.347407
- mask mAP@50: 0.064427
- mask mAP@50:95: 0.008505
- no predicted mask: 7/8
- normal false positives: 0/2

The all-image IoU/Dice are strongly affected by correctly empty normal images. Damage-only overlap worsened, tear/crushed-corner remained missed, and the experiment showed high variance/incipient overfitting. The adapted checkpoint is retained only as an experimental artifact and **must not replace the production model**.

## Known limitations
- one product category
- visible external damage only
- public-pilot segmentation accuracy is modest
- synthetic-controlled data are not a substitute for genuine-camera validation
- synthetic-controlled test set contains only two images per damage class
- crushed-corner and dent/crush collapse to the public checkpoint's native `squeeze` class during adaptation
- corner-vs-dent mapping remains heuristic
- image quality and domain shift affect confidence
- no inference about internal damage, causality, responsibility, fraud or authenticity
- human reviewer owns the final decision

## Required future validation
- genuine-camera project-controlled capture with more independent boxes/sessions
- genuine polygon masks
- non-box negatives for category specificity/FAR
- held-out real-camera segmentation metrics
- failure-case review under realistic lighting/background variation

