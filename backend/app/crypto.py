"""Exact-payload Ed25519 envelopes; uploaded keys are never trusted."""
import base64
import hashlib
import json
import os
import csv
import subprocess
import re
import math
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(report: dict) -> bytes:
    return json.dumps(report, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


class Signer:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            # Limit the private key directory to this Windows account and SYSTEM.
            try:
                result = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'],
                                         capture_output=True, text=True, check=True)
                sid = next(csv.reader(result.stdout.strip().splitlines()))[1]
                subprocess.run(['icacls', str(directory), '/inheritance:r', '/grant:r',
                                f'*{sid}:(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'],
                               capture_output=True, check=True)
            except (OSError, subprocess.CalledProcessError, IndexError) as exc:
                # Continuing could silently expose or replace a signing key whose ACL
                # cannot be verified. Fail with a clear repair path instead.
                raise PermissionError(
                    f'Cannot secure signing-key directory {directory}. Repair its '
                    'Windows ACLs (take ownership, then grant this account and SYSTEM '
                    'access) before starting FrameSeal.') from exc
        else:
            directory.chmod(0o700)
        keypath = directory / 'signing.key'
        if not keypath.exists():
            key = Ed25519PrivateKey.generate()
            raw = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                    serialization.NoEncryption())
            fd = os.open(keypath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
        self.key = Ed25519PrivateKey.from_private_bytes(keypath.read_bytes())
        public = self.key.public_key().public_bytes(serialization.Encoding.Raw,
                                                    serialization.PublicFormat.Raw)
        self.key_id = digest(public)[:24]
        registry = directory / 'trusted_keys.json'
        if not registry.exists():
            registry.write_text(json.dumps({self.key_id: base64.b64encode(public).decode()}))
        self.registry = json.loads(registry.read_text())
        if self.registry.get(self.key_id) != base64.b64encode(public).decode():
            raise ValueError('Active signing key absent from trusted registry; restore keys/registry')

    def sign(self, report):
        payload = canonical(report)
        return {'format': 'deepfake-report-envelope-v1',
                'payload': base64.b64encode(payload).decode(),
                'signature': base64.b64encode(self.key.sign(payload)).decode()}


REQUIRED = {'report_id', 'schema_version', 'video', 'analysis', 'model', 'coverage',
            'thresholds', 'aggregation', 'analyzed_at', 'signing_key_id',
            'sharing_policy', 'limitations'}


def verify(envelope: dict, video: bytes, registry: dict):
    if not isinstance(envelope, dict) or envelope.get('format') != 'deepfake-report-envelope-v1':
        raise ValueError('Unsupported report envelope')
    payload = base64.b64decode(envelope.get('payload', ''), validate=True)
    if len(payload) > 256_000:
        raise ValueError('Report payload too large')
    report = json.loads(payload)
    if (not isinstance(report, dict) or not REQUIRED <= report.keys()
            or type(report['schema_version']) is not int or report['schema_version'] != 1):
        raise ValueError('Invalid report structure/version')
    if not isinstance(report['report_id'], str) or not re.fullmatch('[a-f0-9]{32}', report['report_id']):
        raise ValueError('Invalid report identifier')
    if any(not isinstance(report[field], dict) for field in ('model', 'coverage', 'thresholds', 'sharing_policy')):
        raise ValueError('Invalid report sections')
    if (not isinstance(report['aggregation'], str) or not isinstance(report['limitations'], list)
            or any(not isinstance(v, str) for v in report['limitations'])
            or type(report['sharing_policy'].get('allowed')) is not bool):
        raise ValueError('Invalid policy or limitations')
    if not isinstance(report['analyzed_at'], str) or datetime.fromisoformat(report['analyzed_at']).utcoffset() != timedelta(0):
        raise ValueError('Analysis timestamp must be UTC')
    if not isinstance(report['video'], dict) or not isinstance(report['analysis'], dict):
        raise ValueError('Invalid video or analysis structure')
    h = report['video'].get('sha256')
    n = report['video'].get('byte_length')
    if not isinstance(h, str) or len(h) != 64 or any(c not in '0123456789abcdef' for c in h):
        raise ValueError('Invalid SHA-256')
    if type(n) is not int or n < 1 or not isinstance(report['signing_key_id'], str):
        raise ValueError('Invalid byte length or key identifier')
    assessment = report['analysis'].get('assessment')
    if assessment not in ('Low detected manipulation risk', 'Suspicious', 'Inconclusive'):
        raise ValueError('Invalid assessment')
    score = report['analysis'].get('score')
    if score is not None and (type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1):
        raise ValueError('Invalid model score')
    if not re.fullmatch('[a-f0-9]{24}', report['signing_key_id']):
        raise ValueError('Invalid signing key identifier')
    signature = envelope.get('signature')
    status = 'Unverified: missing signature'
    trusted = registry.get(report['signing_key_id'])
    valid = False
    if signature:
        if not trusted:
            status = 'Invalid: untrusted signing key'
        else:
            try:
                Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted, validate=True)).verify(
                    base64.b64decode(signature, validate=True), payload)
                valid, status = True, 'Valid signature from a trusted service key'
            except (InvalidSignature, ValueError, TypeError):
                status = 'Invalid signature'
    return {'signature_valid': valid, 'signature_status': status,
            'hash_matches': digest(video) == h and len(video) == n,
            'signed_ai_assessment': assessment if valid else None,
            'claimed_ai_assessment': assessment, 'report_id': report['report_id']}
