# Architecture

## Project boundaries

- `backend/app/asgi.py` exposes the FastAPI app built in `backend/app/main.py`.
- `backend/app/main.py` owns API routes, request limits, sessions, CSRF checks, and serving the production React build.
- `backend/app/service.py` handles SQLite records, report creation, eligibility, sharing, and revocation.
- `backend/app/worker.py` runs inference in a disposable timed subprocess.
- `backend/app/detector.py` performs video decoding, frame sampling, MTCNN preprocessing, CPU EfficientNet inference, and score aggregation.
- `backend/app/crypto.py` hashes original bytes and signs/verifies canonical report payloads.
- `backend/app/config.py` loads settings from `backend/config.json` or defaults; `backend/app/model_spec.py` records the pinned detector.
- `backend/app/_vendor/` holds the reviewed MTCNN source and its attribution/license.
- `frontend/` contains the React/Vite client. The Vite development proxy forwards `/api` and share video/report requests to FastAPI. A production Vite build is served by the backend.

## Request flow

1. The React app calls `/api/session` to receive a CSRF token and establish an HttpOnly owner cookie.
2. The client uploads a video to `/api/analyze`. The backend enforces limits and writes original bytes to a random path in `backend/runtime/videos/`.
3. The service hashes the original bytes, runs detection, checks the bytes again, builds the versioned report, signs its canonical payload, and persists the envelope in SQLite.
4. The React client displays the AI assessment and coverage separately from the exact-file digest. Failed or unavailable inference stays inconclusive.
5. The analysis response includes small annotated JPEGs of the exact sampled frames. These previews are returned to the browser but are not stored or included in the signed report. When `OLLAMA_API_KEY` is configured, the owner can also request an optional AI narrative from report metrics; the backend does not send video bytes or frames to that service. The narrative is not model feature attribution.

## Sharing and verification

Sharing is allowed only when the backend policy accepts the signed low-risk result and adequate coverage. The backend rechecks the stored report signature and video hash when issuing a token and on each recipient request. Revocation blocks later requests for the page, video, and report.

Recipient verification checks the signature against the trusted public-key registry and hashes the received file bytes independently. A valid signature authenticates the service's report, not whether the video depicts a genuine event.

## Persistence

`backend/runtime/records.sqlite3` stores report and share state. `backend/runtime/videos/` stores original uploads. `backend/runtime/keys/` stores the signing key and trusted public keys. These remain private and ignored by Git. The schema is initialized at startup; no migration framework or multi-user account system is present.
