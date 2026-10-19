# Architecture

## Components

- `app/asgi.py` exposes the FastAPI app created by `app/main.py`.
- `app/main.py` configures middleware and routes, validates uploads, and serves the templates and static UI in `app/`.
- `app/service.py` owns the SQLite records, private report ownership, worker invocation, report creation, share eligibility, share tokens, integrity checks, and revocation.
- `app/worker.py` runs detection in a disposable subprocess with a wall-clock timeout.
- `app/detector.py` decodes video, samples frames, runs MTCNN face detection and preprocessing, invokes the pinned CPU EfficientNet-B7 checkpoint, and aggregates face scores.
- `app/crypto.py` computes SHA-256 digests, creates Ed25519 signed envelopes using canonical JSON payload bytes, and verifies report/signature/hash independently.
- `app/config.py` defines bounded settings, loaded from project-root `config.json` when present or defaults otherwise. `app/model_spec.py` records pinned model metadata.
- `app/_vendor/` contains the reviewed MTCNN implementation and safe face-weight loader. Its README and license preserve provenance and attribution.

## Analysis and report flow

1. The browser starts a private session and sends an upload with the session's CSRF token. Request and file sizes are bounded; the supplied filename is not used as a storage path.
2. The API writes original bytes to a random server-generated path under `runtime/videos/` and asks the service to analyze them.
3. The service hashes the exact bytes, invokes the worker, and checks the bytes again after analysis. A changed file is rejected.
4. Detection samples unique, evenly spaced frames. MTCNN finds faces; accepted crops are converted to RGB, aspect-preserving resized/padded, normalized, and scored by the pinned model. Maximum score and face/frame coverage produce a low-risk, suspicious, or inconclusive assessment. Failures remain unavailable/inconclusive.
5. The service records the model metadata, score, coverage, thresholds, policy and limitations in a version-1 report. The complete report is serialized as sorted compact UTF-8 JSON and signed. The SQLite database stores the signed envelope and an owner hash; the original video remains in the private runtime directory.

## Verification and sharing

Recipient verification decodes the exact payload bytes, validates report structure, checks the Ed25519 signature against the configured trusted-key registry, and hashes the received video bytes. The response reports signature validity and file-hash equality separately; only a valid signature authenticates the assessment claim.

Sharing is permitted only for a signed low-risk result with an available detector, score within the configured low threshold, adequate analyzed-frame coverage, enough analyzed frames, and no rejected faces. The backend recomputes the policy and verifies the stored envelope and video before issuing a token. Each recipient route checks token state and stored-file integrity again. Revocation marks all of a report's share tokens revoked; subsequent page, video, and report requests are rejected.

## Persistence

`runtime/records.sqlite3` stores report envelopes and share state. `runtime/videos/` holds original uploaded bytes. `runtime/keys/` holds the signing key and trusted public-key registry. These runtime paths are ignored by Git and are not exposed as static files. No migrations or multi-user account system are present; the database schema is initialized at startup.
