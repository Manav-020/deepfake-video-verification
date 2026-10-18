# Security design

## Threat model and trust boundaries

FrameSeal is a single-user, localhost course prototype, not an internet-ready service. It assumes an
honest service operator, trusted installed dependencies and OS account, uncompromised signing key,
and sufficient local disk/memory. It defends against accidental file changes, report tampering, uploaded
untrusted public keys, guessing private record IDs, cross-session report access, trivial cross-site form
submissions, and direct API attempts to bypass sharing policy. It does not defend against malware or an
administrator controlling the service, memory/disk, the browser session, or trusted key registry.

The AI component is fallible and not a security oracle. A manipulator may evade detection, exploit
sampling gaps, or use unseen forgery methods. There is no claim to identify cloned audio, truth, an
original recorder, legal ownership or consent. A correctly signed false negative is still possible.

## File binding and signing

Upload filenames are discarded. Each file receives a random server-generated 128-bit hex identifier
and an exclusively created storage name under `runtime/videos/`. Files have no replacement endpoint.
Analysis runs only after upload finishes. SHA-256 and byte length cover every byte, not decoded frames.
The original hash is compared again after analysis. A changed file prevents report commitment.

A schema-version-1 report contains its ID, exact video digest/length, assessment/model score and
availability, model ID/pinned checksum/preprocessing version, detailed coverage and timestamps,
threshold settings and validation status, aggregation rule, UTC analysis time, signing key ID, sharing
policy and limitations. Canonical UTF-8 JSON is produced with sorted keys, compact separators and
nonfinite floats forbidden. Ed25519 signs those complete payload bytes.

The downloadable envelope carries a format identifier, base64 payload bytes and base64 signature.
Verification authenticates **the exact decoded bytes**, never a reconstructed/reformatted JSON object.
Changing envelope indentation is harmless; changing payload bytes invalidates the signature.
All report fields, including assessment/hash/policy, are covered. Envelopes do not contain a trusted
public key, and uploading one cannot establish trust.

The verifier independently reports trusted signature validity, digest+length equality, and authenticated
AI assessment. An invalid/missing/untrusted signature suppresses the authenticated assessment; an
unsigned claimed assessment is not promoted to trusted evidence. A missing signature means unverified,
not fake. An unchanged signed report can remain signature-valid when paired with a different video;
the separate hash check then fails. Recompression, transcoding, metadata edits, trimming and appended
bytes all change the digest. Sharing distributes the exact analyzed bytes with no transcoding.

## Key lifecycle and trust registry

On first startup, the service creates one Ed25519 private key using exclusive creation. It is persisted
at `runtime/keys/signing.key`, outside static/public content, and reused on every restart. It is never
included in a report, API response, static route or log. Do not commit, share or paste it.
The directory ACL on Windows permits only the current user and SYSTEM; POSIX uses mode 0700 for
the directory and 0600 at key creation. ACL setup failure stops startup. Same-account malware and OS
administrators remain trusted; the key is unencrypted on disk for unattended local use.

The public key is registered on first initialization in `runtime/keys/trusted_keys.json`. Its identifier
is the first 24 hexadecimal characters of SHA-256(public raw bytes). Startup requires the active key
to match its registry entry. Uploaded reports only select among configured keys; unknown key IDs fail.
Registry and private-key state persist separately from generated reports. Back both up securely; a lost
key cannot reproduce the old signing identity. Deleting/regenerating it would invalidate prior trust.
Rotation/recovery is deliberately manual, not silently automatic.

To verify on a separate installation, export public information only:

```powershell
.\.venv\Scripts\python.exe scripts\export_public_keys.py
```

Exchange the key ID and public key over an authenticated channel, compare the ID independently,
then the recipient/operator deliberately adds that base64 raw public key to their own
`runtime/keys/trusted_keys.json` **without removing their active key**, and restarts. Do not import a
key from an unverified uploaded report. No public trust-on-first-use upload endpoint is supplied.
Verification on the same running service needs no manual key setup.

## Sharing policy and access

Uploads and reports are private by default. A random 256-bit HttpOnly SameSite=Strict browser cookie
acts as an owner capability; only its hash is stored alongside report records. Private history/report,
share and revoke operations require ownership. There are no accounts or session recovery. A stolen
cookie grants that session’s capabilities; clearing it loses access. Use one local browser account.

Every state-changing request also requires an HMAC CSRF token derived from the session and a
domain-separated persistent secret; the private key itself is never returned. Origin, when present,
must match the Host. Trusted-host checks limit DNS-rebinding targets to localhost addresses.
No permissive CORS policy is enabled. Requests without a valid session/token fail before uploads.

Share creation is enforced server-side. It requires a signed low-risk assessment, available detector,
acceptable score and coverage, zero rejected faces, and signed allow decision. Stored payload signature
and file hash/length are checked before creating a share. Suspicious, inconclusive, failed or missing-model
results cannot bypass the policy by calling the API or enabling a disabled button.

Links use `secrets.token_urlsafe(32)` (256 random bits); share state is stored in SQLite. Dedicated routes
serve the page, file and report. Each request checks nonrevoked state and integrity; a replaced/corrupt
stored video is refused. Bytes are read and verified as a snapshot before response, avoiding a file-open
replacement window between checking and sending. The threat model excludes malicious operator changes
during inference that deliberately restore bytes before checks. Local administrators are not sandboxed.

Owner revocation disables every existing token for the report. Page, video and report all then return
404. It cannot stop an already started response or recall downloaded copies. There are no public
upload listings or arbitrary filesystem routes. Localhost links require this computer; network hosting
and unrelated platforms are outside this policy’s control. No public deployment was performed.

## Bounded processing and web defenses

An ASGI body limiter counts actual incoming bytes, including chunked bodies, before multipart parsing;
content length is checked early. Per-file streaming reads enforce the upload/report limits too. Report
envelopes are capped at 384 KB and decoded payloads at 256 KB. Structure/version/hash/length and
assessment fields are checked. Malformed input receives a controlled error. Video media is validated
by OpenCV decoding rather than its name/extension. A failed decode receives an inconclusive result.

Duration, dimensions, unique frame samples, faces/frame, minimum face size/confidence, thread count,
and subprocess wall time are bounded. Extra/rejected faces block low risk rather than disappearing
from coverage. A single analysis semaphore rejects concurrent work with 429; the worker is disposable
and killed after timeout. No user filename is passed to a shell; subprocess argument arrays use only
server paths/configuration. This is not a formal codec sandbox or hard RAM quota; hostile codec parser
vulnerabilities, disk exhaustion over many sequential uploads and resource contention remain risks.

The interface uses no third-party scripts/fonts, injects report text with `textContent`, and uses restrictive
Content-Security-Policy, nosniff, no-store, no-referrer and frame-denial headers. A fixed video content type
prevents uploaded HTML execution. Browser codec support is not guaranteed; downloads remain exact.
HTTP localhost uses a non-Secure session cookie because no TLS is configured. Public deployment would
require HTTPS/Secure cookies, proper authentication/recovery, quotas, isolation, key management,
trusted-host/network configuration, retention controls, monitoring and a fresh security review.

## Evidence and known limits

Meaningful automated tests cover unchanged/tampered reports, video hash mismatch, unknown key rejection,
key persistence, policy gates/direct API bypass attempts, ownership/CSRF, changed storage, revocation,
corrupt and missing-model paths, size limits, timeout handling, aggregation and evaluation leakage checks.
A real-model browser smoke covers a generated portrait-video workflow, cryptographic tampering and
revocation. No penetration test, independent cryptographic audit or real/fake benchmark is claimed.

The model/readiness indicator verifies local checkpoint hashes; successful loading and inference are
checked by smoke commands, while per-request failures fail closed. Pinned sources/checksums improve
repeatability but do not establish authenticity of training data or eliminate supply-chain risk.
Reports are custom JSON, with no C2PA implementation or compliance claim.
