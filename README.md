# FrameSeal

FrameSeal is a local video screening and verification application. It combines experimental facial-manipulation screening with a cryptographically signed report bound to the exact uploaded video bytes. AI output is an estimate, not proof that a video is real or fake. A valid signature and matching file hash establish report integrity and file association, not that the video depicts a genuine event.

## Implemented

- FastAPI web UI for private uploads, analysis, history, sharing, revocation, and recipient verification.
- CPU MTCNN face detection and preprocessing with a pinned EfficientNet-B7 TorchScript checkpoint.
- SHA-256 hashing of original uploaded bytes and Ed25519 signatures over canonical report payloads.
- Separate signature, video-hash, and authenticated AI-assessment verification results.
- SQLite persistence, backend-enforced eligible-sharing policy, file checks during sharing and retrieval, and revocation.
- A labeled-video evaluator with validation/test split and leakage checks.

There is no labeled dataset in this repository, and no precision, recall, F1, ROC-AUC, or generalization result has been measured. The detector score is not a calibrated probability. Audio detection, temporal modeling, factual verification, and public deployment are outside scope.

## Setup

Install dependencies from `requirements.txt` in your preferred Python environment. The model checkpoint and MTCNN weights are separate assets; their download scripts verify pinned checksums. This checkout does not include the model checkpoint or Torch in its virtual environment, so real inference requires those assets and dependencies. MTCNN implementation files are vendored under `app/_vendor/` with their MIT license retained.

## Run

```sh
python -m uvicorn app.asgi:app --host 127.0.0.1 --port 8000 --workers 1
```

Open http://127.0.0.1:8000/. Keep the same browser session for private history and sharing controls. The app binds to localhost by default.

## Tests and evaluation

```sh
python -m pytest -q
```

For model integration smoke checks, see [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md). The repeated portrait fixture is not a labeled real/fake benchmark. To evaluate authorized labeled videos, follow [`datasets/README.md`](datasets/README.md) and [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Documentation

- [Architecture](docs/ARCHITECTURE.md): implemented components and data flow.
- [Security](docs/SECURITY.md): trust boundaries, key management, uploads, and sharing.
- [Evaluation](docs/EVALUATION.md): model provenance, data requirements, protocol, and unmeasured performance.

## Limitations

Face sampling can miss manipulated content or faces; max-score aggregation can increase false positives. Thresholds and coverage rules are provisional. The application has no audio analysis, identity tracking, formal codec memory sandbox, account recovery, or public hosting controls. Sharing revocation blocks future link requests but cannot recall downloaded copies. See the security and evaluation documents before interpreting any result.
