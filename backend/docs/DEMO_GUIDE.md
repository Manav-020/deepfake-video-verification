# Integration demonstration

Start the backend and React frontend using the [root README](../../README.md). Run commands below from `backend/`.

## Model screening and sharing

Run `python scripts/smoke_model.py` to create a short video from a repeated public-domain portrait and pass it through MTCNN and EfficientNet. It is an integration fixture, not labeled real/fake evaluation data. A low-risk result does not validate detector performance.

Use the UI to upload a video, inspect its assessment and coverage, create an eligible share, download the exact original bytes and signed report, and revoke the link. Recipients can download both files and verify them in the main UI.

## File and report tampering

Keep the original file and report. Make a byte-modified copy; verification should report a valid report signature and a mismatching video hash. Change a report payload without resigning it; verification should report an invalid signature and withhold its authenticated assessment.

## Browser workflow

With the backend running and Playwright available in the chosen Python environment, run `python scripts/smoke_browser.py`. The browser smoke exercises real-model upload, sharing, recipient verification, report/video tampering, revocation, and responsive layout. It requires the checkpoint and MTCNN assets to be installed.