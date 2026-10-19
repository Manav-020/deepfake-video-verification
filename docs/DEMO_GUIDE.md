# Five-minute demonstration

Start the application with the command in the [README](../README.md) and open http://127.0.0.1:8000/.
Explain first: facial-manipulation screening is experimental; cryptography authenticates the service’s
report and exact file, not the real-world truth of its content.

## Normal analysis and sharing

Run `.\.venv\Scripts\python.exe scripts\smoke_model.py` to create `artifacts/portrait-smoke.mp4`,
or use a short face video you have permission to process. The portrait fixture is a repeated public-domain
NASA photograph, **not real/fake detection evaluation data**. Upload and wait for analysis. Inspect
the assessment, maximum face score, coverage timestamps, model checksum and signed policy.
The installed model returned low risk for the provided fixture; arbitrary videos may be inconclusive.

For an eligible low-risk result create a share link. Open it locally and download the exact video and
signed report. Verify both on the home page: signature valid, hash matches, signed assessment shown.
Explain why these are three separate findings. Revoke links and show that all shared routes stop working.

## Facial deepfake screening

Use an authorized manipulated face video from your requested dataset, with its corresponding original
where available. Follow [the evaluation guide](EVALUATION.md) for access and labeling. Upload both and inspect their scores,
coverage and assessment without preannouncing what result the model must return. A known deepfake can
be missed; inconclusive or even low risk is a limitation to report, not a reason to edit the output.
Suspicious and inconclusive reports must have no enabled share link. No labeled deepfake demo clip is
bundled, and no detection success on such data has been measured for this installation.

## Video tampering

Keep the original report unchanged. Make a byte-modified copy without changing the original:

```powershell
@'
from pathlib import Path
p = Path('artifacts/portrait-smoke.mp4')
Path('artifacts/modified.mp4').write_bytes(p.read_bytes() + b'changed bytes for demo')
'@ | .\.venv\Scripts\python.exe -
```

Verify `modified.mp4` with the original report. Expected: trusted signature still valid, video hash
mismatch. Recompression has the same exact-file mismatch consequence even when it looks identical.

## Report tampering

Download the signed report as `artifacts/signed-report.json`, then alter its payload without resigning:

```powershell
@'
import base64, json
from pathlib import Path
p = Path('artifacts/signed-report.json')
envelope = json.loads(p.read_text())
report = json.loads(base64.b64decode(envelope['payload']))
report['analysis']['reason'] = 'Changed after signing'
envelope['payload'] = base64.b64encode(json.dumps(report).encode()).decode()
Path('artifacts/tampered-report.json').write_text(json.dumps(envelope))
'@ | .\.venv\Scripts\python.exe -
```

Verify the original video against the tampered report. Expected: signature invalid; claimed AI content
is not shown as authenticated. Altering whitespace outside the payload is not payload tampering.

## Repeatable automated demonstration

With the server running and Playwright installed as documented:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_browser.py
```

This performs real-model UI screening, sharing/download checks, video/report tampering and revocation,
and writes screenshots plus `artifacts/browser-smoke.json`. For missing-model behavior, unit tests verify
fail-closed handling without moving your downloaded checkpoints. Never replace the model with fake scores.
