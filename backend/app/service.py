import json
import sqlite3
import subprocess
import sys
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from .config import ROOT
from .crypto import Signer, digest, verify
from .model_spec import metadata

LIMITATIONS = [
    'Experimental facial manipulation screening; thresholds are provisional and not locally validated.',
    'Model scores are not guaranteed probabilities. Sampling may miss manipulated frames or undetected faces.',
    'No audio cloning detection, factual truth assessment, identity or camera-origin authentication.',
    'A signature proves this service signed the report; it does not prove the video is genuine.',
    'Any byte change, including recompression, breaks the exact-file hash match.',
]


def run_detector(path, settings):
    try:
        completed = subprocess.run([sys.executable, '-m', 'app.worker', str(path),
                                    json.dumps(settings.dict())], cwd=ROOT,
                                   capture_output=True, text=True,
                                   timeout=settings.analysis_timeout_seconds)
        message = json.loads(completed.stdout.strip())
        if not message['ok']:
            return {'assessment': 'Inconclusive', 'score': None, 'reason': message['error'],
                    'detector_available': False, 'coverage': {}}
        return message['result']
    except (subprocess.TimeoutExpired, ValueError, KeyError):
        return {'assessment': 'Inconclusive', 'score': None,
                'reason': 'Analysis failed or timed out; try a shorter standard MP4',
                'detector_available': False, 'coverage': {}}


class Service:
    def __init__(self, root: Path, settings, detector=None):
        self.root, self.settings = root, settings
        self.detector = detector or run_detector
        (root / 'videos').mkdir(parents=True, exist_ok=True)
        self.signer = Signer(root / 'keys')
        self.lock = threading.BoundedSemaphore(1)
        with self.db() as con:
            con.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, owner TEXT NOT NULL, envelope TEXT NOT NULL)')
            con.execute('CREATE TABLE IF NOT EXISTS shares (token TEXT PRIMARY KEY, report_id TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0)')

    def db(self):
        return sqlite3.connect(self.root / 'records.sqlite3', timeout=10)

    def finish(self, identifier, owner, path):
        original = path.read_bytes()
        video_hash = digest(original)
        result = self.detector(path, self.settings)
        if digest(path.read_bytes()) != video_hash:
            raise ValueError('File changed during analysis; report refused')
        assessment = result['assessment']
        coverage = result.get('coverage', {})
        requested = coverage.get('requested_frames', self.settings.sample_frames)
        covered = coverage.get('analyzed_frames', 0)
        allowed = (assessment == 'Low detected manipulation risk'
                   and result.get('detector_available') is True
                   and result.get('score') is not None
                   and 0 <= result['score'] <= self.settings.low_threshold
                   and covered >= self.settings.min_analyzed_frames
                   and requested > 0 and covered / requested >= self.settings.min_coverage
                   and coverage.get('analyzed_faces', 0) >= covered
                   and coverage.get('rejected_faces', 0) == 0)
        report = {'report_id': identifier, 'schema_version': 1,
                  'video': {'sha256': video_hash, 'byte_length': len(original)},
                  'analysis': {k: v for k, v in result.items() if k != 'coverage'},
                  'model': metadata(), 'coverage': result.get('coverage', {}),
                  'thresholds': {**self.settings.dict(), 'validation': 'provisional / unvalidated'},
                  'aggregation': 'Maximum model score across ALL quality-eligible detected faces and sampled frames; any rejected face blocks low risk; no identity tracking',
                  'analyzed_at': datetime.now(timezone.utc).isoformat(),
                  'signing_key_id': self.signer.key_id,
                  'sharing_policy': {'allowed': allowed, 'version': 1,
                                     'reason': 'Signed low-risk assessment required'},
                  'limitations': LIMITATIONS}
        envelope = self.signer.sign(report)
        # Verify our exact stored payload before committing a record.
        if not verify(envelope, original, self.signer.registry)['signature_valid']:
            raise ValueError('Report signing failed')
        with self.db() as con:
            con.execute('INSERT INTO reports VALUES (?,?,?)', (identifier, owner, json.dumps(envelope)))
        return {'report': report, 'envelope': envelope}

    def record(self, identifier, owner=None):
        with self.db() as con:
            row = con.execute('SELECT owner,envelope FROM reports WHERE id=?', (identifier,)).fetchone()
        if not row or (owner is not None and row[0] != owner):
            raise LookupError('Report not found')
        envelope = json.loads(row[1])
        import base64
        report = json.loads(base64.b64decode(envelope['payload']))
        return report, envelope

    def checked_file(self, report, envelope):
        try:
            data = (self.root / 'videos' / (report['report_id'] + '.bin')).read_bytes()
        except OSError as exc:
            raise ValueError('Stored video unavailable; sharing refused') from exc
        verified = verify(envelope, data, self.signer.registry)
        if not verified['signature_valid'] or not verified['hash_matches']:
            raise ValueError('Stored video/report integrity check failed')
        if (report['sharing_policy'].get('allowed') is not True
                or report['analysis'].get('assessment') != 'Low detected manipulation risk'
                or report['analysis'].get('detector_available') is not True):
            raise PermissionError('Sharing is blocked by the signed server policy')
        return data

    def share(self, identifier, owner):
        report, envelope = self.record(identifier, owner)
        self.checked_file(report, envelope)
        token = secrets.token_urlsafe(32)
        with self.db() as con:
            con.execute('INSERT INTO shares VALUES (?,?,0)', (token, identifier))
        return token

    def shared(self, token):
        with self.db() as con:
            row = con.execute('SELECT report_id FROM shares WHERE token=? AND revoked=0', (token,)).fetchone()
        if not row:
            raise LookupError('Share link not found or revoked')
        report, envelope = self.record(row[0])
        return report, envelope, self.checked_file(report, envelope)

    def revoke(self, identifier, owner):
        self.record(identifier, owner)
        with self.db() as con:
            con.execute('UPDATE shares SET revoked=1 WHERE report_id=?', (identifier,))
