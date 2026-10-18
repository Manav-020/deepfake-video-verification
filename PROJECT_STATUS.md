# Project status

Last updated: 2026-10-18. Local implementation complete and exercised; labeled evaluation and GitHub
publication remain dependent on user access/authentication.

## Implemented

- FastAPI local web application with responsive HTML/CSS/JS upload, results, sharing, received-video
  verification, readiness and private history. SQLite stores exact signed report envelopes, owner hashes
  and revocable share tokens. Upload filenames never control storage paths.
- Actual CPU MTCNN + DFDC-trained EfficientNet-B7 inference. Checkpoint pinned, downloaded, checksum
  verified and loaded. Original preprocessing/class mapping inspected and matched. Bounded sampling,
  every detected face considered, quality/count rejections recorded, timestamps/scores/coverage captured.
- SHA-256 over exact bytes; before/after integrity checks; complete versioned Ed25519 report signing;
  persistent private key and operator-controlled public-key registry. Windows key directory ACL verified:
  current user and SYSTEM only.
- Private uploads, backend ownership/CSRF/host checks, upload/report limits, bounded subprocess analysis,
  unavailable/corrupt/no-face/error handling. Only signed low-risk results with adequate coverage can share.
  Integrity checked at share creation and recipient access; revocation blocks all three shared routes.
- Repeatable setup/download/run/test/smoke scripts; labeled-video CSV evaluator with split/group leakage
  checks and video-level precision/recall/F1/confusion matrix/ROC-AUC plus explicit abstention handling.
- README, model/data record, security design, exact user actions and demo guide.
- Git initialized on main using the preexisting configured identity; no user files/history/remotes existed.

## Actually tested

Environment: Windows x64, Python 3.13.5, project-local `.venv`, Torch 2.10.0+cpu,
Torchvision 0.25.0+cpu, OpenCV 4.12.0.88, NumPy 2.2.6. No GPU required.

- `python -m pytest -q`: **18 passed**. Tests cover report/signature tampering, changed video bytes,
  unknown keys, missing signatures, persistent keys, eligible-only shares/direct API bypass attempts,
  ownership/CSRF, changed storage/during-analysis rejection, revoked page/video/report routes, malformed/
  oversized/empty uploads, corrupt decode, unavailable model/timeouts, multi-face aggregation, and
  evaluation arithmetic/group leakage. Policy isolation uses explicit test doubles; production never does.
- `python -m pip check`: **No broken requirements found**. An initially tried facenet-pytorch no-deps
  install had old package constraints and a missing-import failure; it was removed. Two reviewed MIT
  MTCNN modules are vendored with license and safe pinned weight loading, avoiding dependency overrides.
- B7 checkpoint SHA-256 verified:
  `e36197ae83fa7c050e8ceba267a1f028f2d74d8ad805bf5d5037a26e8ca96c13`.
  Three MTCNN hashes verified. TorchScript load/shape smoke returned finite `[1,1]` output.
- `scripts/smoke_model.py`: **real face pipeline passed**. Four-second/24-frame MP4 from a repeated
  public-domain NASA portrait; 12 sampled frames/faces; max score **0.04333699**, provisional low risk.
  This is generated integration material, not a labeled video benchmark or accuracy measurement.
- `scripts/check_edge_cases.py`: **real pipeline passed**. Black video -> inconclusive, no analyzed faces;
  two-portrait video -> both faces analyzed on all 12 samples (24 face inferences).
- Local Uvicorn server and Chromium browser automation: actual model upload, signing, share creation,
  exact-byte download, valid signature/matching hash, modified-video mismatch with valid report signature,
  modified-report signature failure, and revocation (all three routes 404): **passed**.
- Desktop/mobile screenshots generated and inspected; mobile overflow check passed; no JavaScript
  errors. Local evidence: ignored `artifacts/model-smoke.json`, `edge-smoke.json`, `browser-smoke.json`
  and screenshots. Shared-route HTTP retrieval checked; playback varies by browser codec support.
- Real server restart preserved signing key ID; key ACL checks passed. `compileall` succeeded.
  Evaluator invocation without the absent manifest exits with a missing-file error, not fabricated metrics.

One upstream Starlette/AnyIO deprecation warning remains in tests; assertions pass.
Playwright's first installer used its shared Windows browser cache and removed two versions it marked
unused; this avoidable tooling side effect was disclosed. Subsequent download instructions use local
`tools/playwright`. No global Python packages or system security settings were changed.

## Remaining work and limitations

- **No labeled dataset attached; no measured detection precision/recall/F1/AUC.** Thresholds are
  provisional. No actual labeled-deepfake classification demo has been validated. Obtain authorized
  data and evaluate before making performance claims.
- Facial frame screening only: no audio cloning, temporal forensic model, truth/provenance guarantee,
  C2PA, identity tracking or formal codec sandbox. Quality uses confidence/pixel size, not calibrated
  blur/pose estimation. Undetected faces and unsampled edits can be missed. CPU only tested.
- Local sessions have no account recovery; revocation cannot recall downloads; retention/disk quotas
  are manual. No public deployment. GPU, fine-tuning and production hosting remain future work.
- **GitHub authentication absent.** Official portable CLI 2.102.0 exists in ignored `tools/gh/gh.exe`;
  auth status reports no authenticated hosts. User login/account selection cannot be completed autonomously.

## Readiness, repository and next actions

Model: **ready, verified and used for actual inference**; no model user action required.
Dataset: **not attached**. Empty validation/test real/fake folders exist. Exact file/manifest/access
instructions are in MODEL_AND_DATA.md, datasets/README.md and USER_ACTIONS_REQUIRED.md.

GitHub repository URL: **none — not created**.
Push status: **not pushed; blocked by GitHub authentication**.
Local source is committed on main; no remote was overwritten and no force-push attempted.
After login, create a NEW PRIVATE repository and verify remote main matches local HEAD; exact commands
are in USER_ACTIONS_REQUIRED.md. Then update this document with the verified URL/push status.

Launch from this directory:
`.\.venv\Scripts\python.exe -m uvicorn app.asgi:app --host 127.0.0.1 --port 8000 --workers 1`.
Open http://127.0.0.1:8000/; use an already-running project server if port 8000 is occupied.
Next user actions: GitHub authentication/publication and legal labeled data acquisition/evaluation.
