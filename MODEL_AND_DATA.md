# Model and data record

Last checked: 2026-10-18. No model training or labeled-video evaluation has been performed here.

## Selected detector and provenance

The detector is TF EfficientNet-B7 Noisy Student fine-tuned for the Deepfake Detection Challenge (DFDC),
published in [Selim Seferbekov’s original solution](https://github.com/selimsef/dfdc_deepfake_challenge),
upstream revision `89c6290490bac96b29193a4061b3db9dd3933e36`.
It is not an unmodified ImageNet classifier or a general AI-image detector.

For a manageable CPU runtime this project uses the
[Facetorch export/model card](https://huggingface.co/tomas-gajarsky/facetorch-deepfake-efficientnet-b7),
repository `tomas-gajarsky/facetorch-deepfake-efficientnet-b7`, pinned revision
`4acc494f37eb63d7457166eff2acb45c5b04b9a6`, artifact `model.pt` (TorchScript, CPU).
Artifact SHA-256: `e36197ae83fa7c050e8ceba267a1f028f2d74d8ad805bf5d5037a26e8ca96c13`.
This file was actually downloaded, checksum verified, loaded with Torch 2.10.0+cpu, and used for face
inference. The card identifies it as upstream `final_777_DeepFakeClassifier_tf_efficientnet_b7_ns_0_31`
and records a tensor-equality provenance check; that equality audit is the exporter’s claim, not a new
audit performed by this project. The upstream checkpoint hash recorded by the card is
`00dd6cd9466cddfd7da7c333d8fecae81593307827093deaf4d7cdf704bc8bfa`.

The upstream repository and export are MIT licensed; export license/notices are downloaded into
`models/LICENSE` and `models/THIRD_PARTY_NOTICES.md`. Model licensing grants no dataset/input rights.
The original training data is DFDC facial-manipulation video data. This installation has not audited
individual training examples or recreated training. Claims from competition results do not transfer to
this application’s single-checkpoint, sampled-video pipeline. No accuracy figure is claimed here.

## Input and output contract

Relevant implementation inspected:
[upstream inference](https://github.com/selimsef/dfdc_deepfake_challenge/blob/89c6290490bac96b29193a4061b3db9dd3933e36/kernel_utils.py),
[training labels](https://github.com/selimsef/dfdc_deepfake_challenge/blob/89c6290490bac96b29193a4061b3db9dd3933e36/training/datasets/classifier_dataset.py),
[MTCNN source](https://github.com/timesler/facenet-pytorch/blob/master/models/mtcnn.py), and the export card.

Preprocessing version: `dfdc-mtcnn-rgb-thirds-isotropic-pad380-imagenet-v1`.

- Decode in OpenCV (BGR), explicitly convert to RGB. Sample unique evenly spaced frame indices.
- MTCNN on half-resolution PIL RGB frames; stage thresholds `[0.7, 0.8, 0.8]` as in upstream inference.
  Restore boxes to source resolution. No eye/landmark alignment or face-recognition transform is used.
- Process all detected faces within limits; require confidence >=0.9 and box width/height >=64 source
  pixels by default. Rejected/surplus faces are recorded and block low-risk classification.
- Expand boxes by one third of their width/height on each side, clipped to image boundaries.
- Resize preserving aspect ratio so longest side is 380 (area downsampling, cubic upsampling), center
  in black 380×380 RGB canvas. This follows original inference, rather than stretching rectangular crops.
- Float32 CHW, divide by 255, ImageNet mean `[0.485,0.456,0.406]` and std `[0.229,0.224,0.225]`.
- Model processes **single face frames**, not temporal sequences. One logit per face; apply sigmoid once.
  Training labels are real=0, fake=1, so larger scores indicate more detected manipulation.
  Sigmoid outputs are model scores, not calibrated or guaranteed probabilities.
- The original solution was an ensemble with its own aggregation. This project uses one verified
  checkpoint and a documented maximum-score policy; it does not reproduce competition performance.

MTCNN sources/weights: [timesler/facenet-pytorch](https://github.com/timesler/facenet-pytorch), MIT,
2.6.0 PyPI wheel SHA-256 `ecb82b27beb226d106f2219efe8f829b01b87a8595badd01545679bdb9f19cca`.
Two reviewed modules and their license are vendored (see `app/_vendor/README.md`); only paths/imports and
checksum-checked safe state-dict loading are changed. Setup extracts only the three weights from that
verified wheel. Individual SHA-256 hashes are recorded in `app/_vendor/face_weights.py` and checked
before loading with `weights_only=True`. No remote Python/custom `trust_remote_code` is executed.
The EfficientNet TorchScript archive’s 726 code entries were extracted and operator-inspected before
loading: standard convolution/normalization/pooling/activation/linear tensor operations, no flagged
process/file execution calls. Only the pinned artifact is accepted.

## Aggregation, coverage and practical limits

Video score = maximum across **all analyzed faces across all sampled frames**. No identity tracking.
Suspicious if any score >=0.8, even when coverage is weak; otherwise low risk only when maximum <=0.2,
at least 4 frames have analyzed faces, at least 75% of requested samples have analyzed faces, and no
detected face is rejected for quality/count limits. All other cases are inconclusive. If inference fails
at any stage, no partial low-risk score is used. Absent/mismatched weights return unavailable/inconclusive.

Face quality is approximated by detection confidence and source-pixel size; there is no calibrated blur,
occlusion or pose estimator. Missed faces cannot be counted and remain a major limitation. Sampling can
miss brief edits. Max aggregation may increase false positives as the number of frames/faces grows.
Settings are configurable but **unvalidated**; low risk does not establish authenticity.

Default limits: 100 MB, 120 seconds, 2,073,600 decoded pixels, 12 frames, up to 8 processed faces/frame,
180-second disposable-worker wall-clock timeout, four Torch CPU threads and one concurrent analysis.
The worker has time/input bounds, not a formal OS memory sandbox. CPU is the supported/tested device;
several GB free RAM is advisable, but peak memory was not benchmarked. GPU support is future work.

## Measured integration outcomes, not detection evaluation

`scripts/smoke_model.py` used a four-second, 24-frame MP4 made from a repeated public-domain NASA
astronaut portrait. Twelve sampled frames/faces completed actual MTCNN + EfficientNet inference;
maximum score 0.04333699, low risk with default thresholds. A browser workflow then analyzed the same
fixture through the real server, created/downloaded a share, verified bytes/signature, rejected report
tampering, detected changed video bytes and revoked the share. These are integration checks only.
The portrait’s source and public-domain status are documented by
[scikit-image](https://scikit-image.org/docs/stable/api/skimage.data.html#skimage.data.astronaut).
This fixture and test doubles are not labeled real/fake video evaluation data.

No precision/recall/F1/AUC, generalization, calibration or robustness performance has been measured.
Do not reuse the smoke score as a detector quality claim.

## Legal data access and expected files

Request [FaceForensics++](https://github.com/ondyari/FaceForensics) using its current Access form and
terms; after approval use the authors’ download script. Needed: original videos, corresponding facial
manipulation videos (e.g. Deepfakes/FaceSwap/Face2Face/NeuralTextures), label/source relationships and
official split metadata. c23 is a manageable starting compression level. Obtain sufficient originals
and fakes in both validation and held-out test sets; document subset selection and identity grouping.

Alternatively request [Celeb-DF-v2](https://github.com/yuezunli/celeb-deepfakeforensics) via its authors’
access process; use real and synthesized videos and its supplied test-list metadata. Follow terms.
DFDC can be obtained via the [official Kaggle competition](https://www.kaggle.com/c/deepfake-detection-challenge/data)
subject to its rules, but training-distribution overlap limits claims of independent generalization.
No credentials, access-control bypass, dataset redistribution or automatic terms acceptance is provided.

Put authorized videos under `datasets/validation/{real,fake}/` and `datasets/test/{real,fake}/`.
Create `datasets/manifest.csv` following `datasets/README.md` with `path,label,split,group` columns.
Related originals, derived fakes, source/target identities and related videos must share a group and
partition. Do not split video frames into independent train/test examples. The evaluator checks exact
file duplicates and explicit groups across partitions; identity labels remain the operator’s responsibility.

## Evaluation protocol

1. Keep validation and held-out test videos and identity families separate. Prefer official splits while
   removing cross-identity leakage where possible; document all departures and compression/subsets.
2. Run validation with the script below. Select thresholds/coverage using validation only. Preserve its
   output/config/checkpoint. Freeze configuration before looking at final test results.
3. Run test once, report sample counts, class balance, manipulation types, coverage and abstentions.

```powershell
.\.venv\Scripts\python.exe scripts\evaluate.py --manifest datasets\manifest.csv --split validation --output artifacts\validation.json
.\.venv\Scripts\python.exe scripts\evaluate.py --manifest datasets\manifest.csv --split test --output artifacts\test.json
```

Precision/recall/F1 and confusion matrix use decided videos only, fake as positive. Abstentions are
excluded, not treated as correct or authentic; their overall/per-class counts and rate are always output.
ROC-AUC uses every finite scored video, including score-bearing inconclusives; unavailable/null-score
videos are excluded. AUC is null if both labels are not represented. Metrics are null when undefined by
absence of decided samples. Conditional metrics can be optimistic under high abstention, so show their
denominators and inconclusive rates. Per-video results preserve reasons/coverage. Unit tests validate
metric arithmetic with artificial records only; that is software testing, not measured model performance.

Version 1 requires no training. Fine-tuning, calibrated thresholds, tracking, stronger face-quality checks,
audio analysis and external independent datasets are future work.
