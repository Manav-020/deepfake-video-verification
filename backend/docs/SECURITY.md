# Security

FrameSeal is a single-user localhost prototype. It assumes the operator, operating-system account, installed dependencies, signing key, trusted-key registry, and local browser session are trusted. It protects against accidental file changes, report tampering, untrusted uploaded keys, cross-session record access, basic cross-site form submission, and direct API attempts to bypass sharing eligibility. It is not an internet-ready service and does not protect against malware, a malicious administrator, or compromise of the machine.

AI assessment and cryptographic verification are separate trust dimensions. The detector can miss manipulations or raise false alarms. A valid signature authenticates that the service key signed the report; a matching SHA-256 and byte length bind that report to the received bytes. Neither demonstrates that the video depicts a genuine event.

## Reports and keys

The SHA-256 digest covers the exact original upload bytes, not decoded or transformed frames. The application checks the file has not changed during inference. Ed25519 signs the complete version-1 report as canonical UTF-8 JSON with sorted keys and compact separators. Verification uses the exact decoded payload bytes; envelope whitespace outside the payload does not alter the signature.

The report does not supply a trusted public key. Verification selects a key from `backend/runtime/keys/trusted_keys.json` by key ID. Missing, unknown, malformed, or invalid signatures do not authenticate the report's AI assessment. The signed report format should not change without compatibility handling.

On first startup the application creates `backend/runtime/keys/signing.key` and a matching public-key registry entry. The key persists across restarts. Windows ACLs are restricted to the current account and SYSTEM; POSIX uses restrictive permissions. The key is unencrypted for local unattended use. Back up the key and registry securely; losing or replacing them breaks continuity with previous reports.

## Uploads and sharing

Uploads receive random server-generated names and remain under `backend/runtime/videos/`. The React UI obtains an HttpOnly SameSite session from `/api/session`; the database stores only its owner hash. Mutating routes require a derived CSRF token, and host, request-body, report, and video limits are enforced. In development, Vite proxies API calls to FastAPI. The inference worker has a wall-clock timeout but is not a formal memory or codec sandbox.

Sharing is private by default. Backend routes require report ownership for private operations. Share creation checks the stored signature, original-file hash, detector availability, and signed low-risk policy. Recipient routes recheck active share state and file integrity. Revocation blocks future access but cannot recall downloads already made.

Localhost uses HTTP without Secure cookies. Do not expose the app publicly without authentication, HTTPS, resource isolation, quotas, retention controls, and a fresh security review. No independent penetration test or cryptographic audit is claimed.

## Optional Ollama explanation

The optional explanation endpoint reads `OLLAMA_API_KEY` from the ignored root `.env` file or backend process environment; process environment values take precedence. The key is sent only from the backend to `https://ollama.com/api/chat`; it is never returned to the browser or written to application logs. The request includes report metrics and assessment text, but not video bytes, frames, or the signed report. This sends those metrics to Ollama Cloud for processing. The generated narrative is not detector evidence, feature attribution, or an authenticity check.
