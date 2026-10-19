# Model and evaluation

## Current state

No labeled video dataset is included, and this checkout has no measured detector precision, recall, F1, confusion matrix, false-positive/negative rate, ROC-AUC, calibration, or generalization results. The current `backend/.venv` lacks Torch and `backend/models/model.pt` is absent, so real-model inference has not been run in this checkout. Existing tests validate software behavior and metric arithmetic only. Do not present integration smoke scores as detection performance.

The selected detector is a CPU TorchScript export of EfficientNet-B7 Noisy Student fine-tuned for the Deepfake Detection Challenge. The pinned model repository is `tomas-gajarsky/facetorch-deepfake-efficientnet-b7`, revision `4acc494f37eb63d7457166eff2acb45c5b04b9a6`; the required `models/model.pt` SHA-256 is `e36197ae83fa7c050e8ceba267a1f028f2d74d8ad805bf5d5037a26e8ca96c13`. The model was sourced from Selim Seferbekov's DFDC solution, upstream revision `89c6290490bac96b29193a4061b3db9dd3933e36`. The export's upstream provenance/equality statement is not a new independent audit by this project. See `app/model_spec.py` and `scripts/download_model.py` for the enforced identifiers and checksum.

The vendored MTCNN implementation derives from `facenet-pytorch` 2.6.0, distributed under MIT terms. The extracted wheel is pinned by SHA-256 `ecb82b27beb226d106f2219efe8f829b01b87a8595badd01545679bdb9f19cca`; its face-weight files are separately checksum-checked. Attribution and local changes are recorded in `app/_vendor/README.md` and `app/_vendor/FACENET_LICENSE.md`.

## Inference contract

- OpenCV decodes BGR video; sampled frames are converted to RGB. Unique evenly spaced indices are used.
- Vendored MTCNN runs at half resolution with thresholds `[0.7, 0.8, 0.8]`; boxes are restored to source coordinates. No landmark alignment or face-recognition transform is applied.
- Faces below the configured confidence/size limits or beyond the per-frame count limit are recorded as rejected. Accepted boxes expand by one third in each direction, are clipped, resized with aspect ratio preserved to a 380-pixel maximum side, and centered on a black 380×380 canvas.
- RGB float tensors use ImageNet mean and standard deviation. The single-face-frame model returns one logit; sigmoid is applied once. Higher scores indicate more manipulation according to the model mapping. Scores are not calibrated probabilities.
- Video score is the maximum over all analyzed faces in sampled frames. Suspicious is assigned at or above 0.8. Low risk requires a score at or below 0.2, at least four analyzed frames, at least 75% frame coverage, and no rejected faces. Other cases are inconclusive. These thresholds and policy are provisional and configurable.

This is a single-checkpoint sampled-frame pipeline; it does not reproduce the original competition ensemble. Unsampled edits, missed faces, domain shift, and max-score false positives are material limitations. CPU is the supported configuration; peak resource use has not been benchmarked.

## Dataset acquisition and layout

No videos or dataset licenses are bundled. Acquire data through the dataset owners' official access procedures and follow their terms. `datasets/README.md` gives manifest format and links to FaceForensics++ and Celeb-DF-v2. Keep originals, derivatives, identities/source relationships, and official split metadata; group related material so groups do not cross validation and test. The evaluator detects identical-file and explicitly declared group leakage, but cannot infer omitted identity relationships.

## Protocol and metrics

1. Choose a legally obtained dataset and document access, subset/compression, class balance, manipulation types, and grouping.
2. Keep validation and held-out test identity/source groups separate. Run validation first and choose thresholds only there.
3. Freeze settings and model/checkpoint details before evaluating the test split.
4. Report per-class counts, coverage, abstention rate, and video-level precision, recall, F1, confusion matrix, false-positive/negative rates, and ROC-AUC when both labels and continuous scores are available. Include inference time and resource measurements for deployment-relevant conditions.
5. Interpret decided-only metrics with their denominators because inconclusive cases are excluded. ROC-AUC includes finite scored videos, including score-bearing inconclusives.

Example commands:

```sh
python scripts/evaluate.py --manifest datasets/manifest.csv --split validation --output artifacts/validation.json
# Set/freeze thresholds from validation only before running held-out test.
python scripts/evaluate.py --manifest datasets/manifest.csv --split test --output artifacts/test.json
```

The evaluator checks manifest paths, duplicate files, and declared group leakage. Evaluation numbers should be documented only after a real labeled run has completed. Unit-test fixtures are synthetic and are not benchmark results.
