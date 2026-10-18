# FrameSeal

**AI-Based Deepfake Video Detection and Cryptographic Verification Before Online Sharing**

A working local Information Security course application: facial-manipulation screening with a real
DFDC-trained detector, SHA-256 binding to exact video bytes, Ed25519 signed reports, private uploads,
policy-controlled sharing, revocation, and independent recipient signature/hash checks.

This is experimental screening. It does not detect cloned audio, establish factual truth, identify a
camera/operator, or guarantee authenticity. Thresholds are provisional; no labeled detection evaluation
has been performed. A custom signed JSON report is used, not C2PA.

## Run on this Windows machine

Dependencies and weights are already installed in this project’s `.venv` and `models` directories.

```powershell
Set-Location -LiteralPath 'D:\coding\python\ISC Project'
.\.venv\Scripts\python.exe -m uvicorn app.asgi:app --host 127.0.0.1 --port 8000 --workers 1
```

Open **http://127.0.0.1:8000/**. Keep the same hostname/browser when managing uploads. Stop with Ctrl+C.
If port 8000 is occupied by the existing project server, use it or stop that server first.
No virtual-environment activation or PowerShell execution-policy change is needed for the command above.

## Fresh setup

Requires Windows x64, Python 3.13 ([official downloads](https://www.python.org/downloads/windows/)),
internet for public wheels/checkpoints, and several GB of free disk/memory. CPU inference is the tested
configuration; CUDA is not required or enabled. The checkpoint is approximately 256 MiB (268 MB).

```powershell
Set-Location -LiteralPath 'D:\coding\python\ISC Project'
.\scripts\setup.ps1
.\scripts\run.ps1
```

If script execution is disabled, run the underlying commands without altering security policy:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe scripts\setup_faces.py
.\.venv\Scripts\python.exe scripts\download_model.py
.\.venv\Scripts\python.exe -m pip check
```

The two reviewed MIT MTCNN source modules are vendored under `app/_vendor` to avoid upstream package
constraints that lack Python 3.13 wheels. No `facenet-pytorch` package or dependency override is needed.
Model setup only downloads a pinned verified artifact and face weights; no repository Python is executed.
The TorchScript archive’s code is extracted to `models/torchscript-code-review.json` for inspection.
Its relevant operators and upstream preprocessing were inspected before this installation’s first load.

## Use the application

1. **Upload and Analyze:** select a video, preferably MP4. Default limits: 100 MB, 120 seconds, 1080p
   pixel area, 12 sampled frames, at most 8 analyzed faces per frame, 180-second processing deadline.
   The UI shows a busy state; detailed frame timestamps and scores appear after completion.
2. **Analysis Results:** read the assessment, model score, reason, coverage and limitations. All detected
   eligible faces contribute. Rejected faces or inadequate coverage prevent low-risk classification.
   Corrupt/unsupported files, missing weights and failed inference produce inconclusive signed records
   where an upload can be retained; empty/oversized requests are rejected outright.
3. **Share Video:** only a signed low-risk result with sufficient coverage and a matching stored file is
   eligible. Create an unguessable link, or revoke all links for that report. Recipients can view/download
   the exact analyzed bytes and signed report. Revocation prevents future access, not downloaded copies.
4. **Verify Received Video:** upload the received video and downloaded report. The UI separately shows
   signature validity, exact-file hash matching, and authenticated AI assessment. A valid signature with
   a hash mismatch means the report is authentic but the received file is different. A missing signature
   is unverified, not fake. Recompression invalidates exact-byte matching.
5. **Readiness:** the status strip shows checkpoint readiness, provisional thresholds and dataset status.
   Readiness checks checksums, not a full inference on every page load; a runtime failure fails closed.

Private report management uses a random HttpOnly, SameSite browser cookie. Clearing it loses access to
that session’s private records and revocation controls; there is no account recovery in this local version.
Localhost share links work only on this computer. This app cannot enforce policies on unrelated platforms.
Codec support varies by browser; download the exact file when inline playback is unsupported.

## Configuration

```powershell
Copy-Item config.example.json config.json
```

Edit `config.json` and restart. All size, duration, frame, face quality, threshold, coverage and time limits
are configurable with safety ceilings on sampling. `config.json` is ignored by Git. The default rule is
maximum face score across sampled frames: <=0.2 with adequate coverage → low risk; >=0.8 → suspicious;
otherwise inconclusive. At least 4 analyzed frames, 75% sampling coverage and no rejected faces are
required for low risk. This is a conservative project policy, not the upstream ensemble aggregation.
Do not tune thresholds against your final test set. Existing reports retain their signed settings/policy.

## Tests and smoke checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\smoke_model.py
```

The smoke script creates `artifacts/portrait-smoke.mp4` from a public-domain NASA portrait and runs
actual face detection and deepfake inference. It is an integration fixture, **not a detection benchmark**.
Use `--video 'path\to\your-authorized-video.mp4'` for an independently supplied video.

For browser checks, launch the server on port 8000 in another terminal, then:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\tools\playwright"
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts\smoke_browser.py
```

This exercises the UI with actual inference, signed sharing, changed-video hash mismatch, report-tampering
failure and revocation. Screenshots/results remain in ignored `artifacts/`. Unit tests use clearly isolated
test doubles only for policy/crypto isolation; normal application detection always uses the real worker.

## Evaluation

Attach legal labeled data following [datasets/README.md](datasets/README.md) and [MODEL_AND_DATA.md](MODEL_AND_DATA.md).

```powershell
.\.venv\Scripts\python.exe scripts\evaluate.py --manifest datasets\manifest.csv --split validation --output artifacts\validation.json
# Choose/freeze config.json thresholds using validation only, then:
.\.venv\Scripts\python.exe scripts\evaluate.py --manifest datasets\manifest.csv --split test --output artifacts\test.json
```

Outputs include video-level precision, recall, F1, confusion matrix, ROC-AUC when defined, per-video
coverage and inconclusive rates. Decided-only metrics explicitly exclude abstentions; ROC uses all
scored videos, including inconclusives. Never interpret these conditional metrics without coverage.
No training or fine-tuning is required. No evaluation numbers are claimed until labeled data is attached.

## Files and trust

- `app/`: FastAPI app, worker, real detector, signing, SQLite records and interface.
- `scripts/`: reusable setup, model/face downloads, run/test, evaluation and smoke commands.
- `runtime/`: private keys, trust registry, database and videos; ignored by Git, never mounted publicly.
- `models/`, `datasets/`, `.venv/`, `tools/`, `artifacts/`: local generated/downloaded material, ignored.

Keep `runtime/keys/signing.key` safe; startup preserves it. On Windows its directory ACL grants only the
current account and SYSTEM; POSIX uses restrictive permissions. Back it up securely with the public
registry. Do not delete the runtime directory to troubleshoot a model: doing so loses signing identity
and data. Unknown key IDs fail authentication. To establish trust on a second installation, deliberately
exchange public keys via an authenticated channel; see [SECURITY_DESIGN.md](SECURITY_DESIGN.md).

## Troubleshooting and handoff

- Detector unavailable: rerun both model setup commands; hashes must match. No fake fallback exists.
- Inference timeout: use a shorter/lower-resolution video or adjust the bounded deadline responsibly.
- No faces/inconclusive: use clear frontal faces with adequate resolution; do not lower thresholds to
  force eligibility. Faces missed by MTCNN and unsampled manipulations remain a known limitation.
- Corrupt/codec error: use a decodable standard MP4 copy, then analyze that exact copy. It has a different
  hash from the source. OpenCV’s MP4 fixture encoder may emit a harmless PNG color-profile warning.
- CSRF error: reload the home page; keep the same localhost hostname and session cookies.
- Key/ACL error: run under the account that created the project; restore the original key/registry rather
  than generating a replacement. The application intentionally stops if its key is absent from trust.
- Tests currently emit one upstream Starlette/AnyIO deprecation warning; assertions pass.
- GitHub is blocked only by missing authentication. A portable official `gh.exe` was downloaded into
  ignored `tools/gh`. See [USER_ACTIONS_REQUIRED.md](USER_ACTIONS_REQUIRED.md) for exact commands.

See [PROJECT_STATUS.md](PROJECT_STATUS.md), [SECURITY_DESIGN.md](SECURITY_DESIGN.md),
[MODEL_AND_DATA.md](MODEL_AND_DATA.md), and [DEMO_GUIDE.md](DEMO_GUIDE.md).
