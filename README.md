# FrameSeal

FrameSeal is a local video screening and verification app. Its FastAPI backend performs experimental facial-manipulation screening, binds a signed report to the exact uploaded video bytes, and supports private history, eligible sharing, revocation, and recipient verification. The React frontend provides the browser interface. An AI assessment is an estimate; a valid signature and matching hash establish report integrity and file association, not that a video depicts a genuine event.

There is no labeled dataset in this repository and no detection-performance result has been measured. Scores are not calibrated probabilities. Audio detection, temporal analysis, factual verification, and public deployment are outside scope.

## Project layout

- `backend/` contains the FastAPI app, detector, cryptography, tests, scripts, runtime data, model/data locations, Python dependencies, and backend docs.
- `frontend/` contains the React/Vite client. Its development proxy connects the browser to the backend API and share endpoints.
- Use your preferred Python environment. The current ignored UV environment is in `backend/.venv/`.

Model checkpoint and MTCNN weights are separate assets. The checksum-verifying download scripts are in `backend/scripts/`; the vendored MTCNN code retains its license under `backend/app/_vendor/`.

## Run locally

Start FastAPI from `backend/` with `python -m uvicorn app.asgi:app --reload --host 127.0.0.1 --port 8000 --workers 1`, then start the React dev server from `frontend/` with `npm run dev`. Open http://127.0.0.1:5173/; Vite proxies API calls to FastAPI. (`app.main` exposes an app factory, so the import target is `app.asgi:app`.)

For a single-server run, build the frontend with `npm run build` from `frontend/`, then start FastAPI from `backend/`; it serves the built React app and API on port 8000.

## Verify and evaluate

Run the Python suite from `backend/` with `python -m pytest -q`. For the model smoke workflow and dataset protocol, see [the demo guide](backend/docs/DEMO_GUIDE.md), [dataset instructions](backend/datasets/README.md), and [evaluation guide](backend/docs/EVALUATION.md). Further details are in the [architecture](backend/docs/ARCHITECTURE.md) and [security](backend/docs/SECURITY.md) guides.
