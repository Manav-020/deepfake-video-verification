# Security

## Threat model and trust boundary

FrameSeal is a single-user localhost prototype. It assumes the operator, operating-system account, installed dependencies, signing key, trusted-key registry, and local browser session are trusted. It protects against accidental file changes, report tampering, untrusted uploaded keys, cross-session record access, basic cross-site form submission, and direct API attempts to bypass sharing eligibility. It is not an internet-ready service and does not protect against malware, a malicious administrator, or compromise of the machine.

AI assessment and cryptographic verification are separate trust dimensions. The detector can miss manipulations or raise false alarms. A valid signature authenticates that the corresponding service key signed the report; a matching SHA-256 and byte length bind that report to the received bytes. Neither demonstrates that the video depicts a genuine event.

## Reports and keys

The SHA-256 digest covers the exact original upload bytes, not decoded or transformed frames. The application checks the file has not changed during inference. Ed25519 signs the complete version-1 report encoded as canonical UTF-8 JSON with sorted keys, compact separators, and non-finite numbers disallowed. Verification uses the exact decoded payload bytes; envelope whitespace outside the payload does not alter the signature.

The report does not supply a trusted public key. Verification selects a public key from `runtime/keys/trusted_keys.json` using the report's key ID. Missing, unknown, malformed, or invalid signatures do not authenticate the report's AI assessment. The signed report format should not be changed without explicit compatibility handling.

On first startup, the application creates `runtime/keys/signing.key` and a matching public-key registry entry. The key persists across restarts. On Windows, the key directory ACL is restricted to the current account and SYSTEM; on POSIX, restrictive directory and file modes are used. The key is unencrypted for local unattended use. Back up the key and registry securely; losing or replacing them breaks continuity with previous reports. Public-key exchange to another installation must use an authenticated channel.

## Upload privacy and web controls

Uploads receive random server-generated storage names and remain under the private runtime directory. The UI uses an HttpOnly SameSite session capability; the database stores its hash with each report. Mutating routes require a derived CSRF token, and same-origin, trusted-host, request-body, report, and video limits are enforced. A disposable worker bounds inference wall time, but this is not a formal memory or codec sandbox. Repeated uploads can consume disk; quotas and retention management are not implemented.

The service serves fixed content types and security headers, and does not mount the runtime directory. Localhost uses HTTP without Secure cookies because TLS is not configured. Do not expose the service to a network without authentication, HTTPS, resource isolation, quotas, retention controls, and a fresh security review.

## Sharing and revocation

Uploads are private by default. Backend routes require report ownership for private operations. Share creation verifies the stored report signature and original file hash/length and enforces the signed low-risk policy plus detector availability and adequate coverage. Recipient page, video, and report routes all check active share state and stored integrity. Revocation blocks future requests on all routes; it cannot cancel an in-flight response or recall copies already downloaded.

## Limitations

There has been no independent penetration test or cryptographic audit. Pinned source/checkpoint checksums improve repeatability but do not establish training-data provenance or remove supply-chain risk. The application makes no claims about identity, consent, truth, audio, or camera origin. The custom JSON report is not C2PA and makes no standards-compliance claim.
