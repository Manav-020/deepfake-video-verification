import base64
import json
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.crypto import Signer, verify, canonical
from app.detector import aggregate, analyze
from app.main import create_app


def detector(assessment='Low detected manipulation risk', available=True):
    def call(path, settings):
        return {'assessment': assessment, 'score': 0.1 if assessment.startswith('Low') else 0.9,
                'reason': 'ISOLATED TEST DOUBLE', 'detector_available': available,
                'coverage': {'analyzed_frames': 12, 'analyzed_faces': 12}}
    return call


def client(tmp_path, assessment='Low detected manipulation risk', available=True):
    app = create_app(tmp_path, Settings(), detector(assessment, available))
    c = TestClient(app)
    c.get('/')
    c.headers['x-csrf-token'] = c.get('/api/session').json()['csrf_token']
    return c, app.state.service


def upload(c, content=b'isolated test bytes'):
    r = c.post('/api/analyze', files={'video': ('test.mp4', content, 'video/mp4')})
    assert r.status_code == 200, r.text
    return r.json()


def test_sign_verify_tamper_and_missing_signature(tmp_path):
    c, service = client(tmp_path)
    result = upload(c)
    env = result['envelope']
    assert verify(env, b'isolated test bytes', service.signer.registry)['signature_valid']
    assert verify(env, b'changed video', service.signer.registry)['hash_matches'] is False
    payload = json.loads(base64.b64decode(env['payload']))
    payload['analysis']['reason'] = 'tampered'
    changed = {**env, 'payload': base64.b64encode(canonical(payload)).decode()}
    assert not verify(changed, b'isolated test bytes', service.signer.registry)['signature_valid']
    missing = {**env, 'signature': None}
    assert verify(missing, b'isolated test bytes', service.signer.registry)['signature_status'].startswith('Unverified')


def test_untrusted_key_and_persistence(tmp_path):
    c, service = client(tmp_path / 'a')
    report = upload(c)['report']
    other = Signer(tmp_path / 'other')
    report['signing_key_id'] = other.key_id
    assert not verify(other.sign(report), b'isolated test bytes', service.signer.registry)['signature_valid']
    public_id = service.signer.key_id
    raw = (tmp_path / 'a/keys/signing.key').read_bytes()
    restarted = create_app(tmp_path / 'a', Settings(), detector()).state.service
    assert restarted.signer.key_id == public_id
    assert (tmp_path / 'a/keys/signing.key').read_bytes() == raw


def test_eligible_share_and_revoke(tmp_path):
    c, service = client(tmp_path)
    result = upload(c)
    identifier = result['report']['report_id']
    link = c.post(f'/api/reports/{identifier}/share').json()['url']
    assert c.get(link).status_code == 200
    assert c.get(link + '/video').content == b'isolated test bytes'
    assert c.get(link + '/report').json() == result['envelope']
    assert c.post(f'/api/reports/{identifier}/revoke').status_code == 200
    for route in (link, link + '/video', link + '/report'):
        assert c.get(route).status_code == 404


@pytest.mark.parametrize('assessment,available', [('Suspicious', True), ('Inconclusive', True),
                                               ('Inconclusive', False), ('Low detected manipulation risk', False)])
def test_direct_backend_cannot_bypass_policy(tmp_path, assessment, available):
    c, _ = client(tmp_path, assessment, available)
    identifier = upload(c)['report']['report_id']
    assert c.post(f'/api/reports/{identifier}/share').status_code == 403


def test_private_ownership_csrf_and_modified_storage(tmp_path):
    c, service = client(tmp_path)
    identifier = upload(c)['report']['report_id']
    route = f'/api/reports/{identifier}/share'
    assert c.post(route, headers={'x-csrf-token': ''}).status_code == 403
    assert c.post(route, headers={'origin': 'https://attacker.example'}).status_code == 403
    stranger = TestClient(c.app)
    stranger.get('/')
    stranger.headers['x-csrf-token'] = stranger.get('/api/session').json()['csrf_token']
    assert stranger.get(f'/api/reports/{identifier}').status_code == 404
    assert stranger.post(route).status_code == 404
    link = c.post(route).json()['url']
    (service.root / 'videos' / (identifier + '.bin')).write_bytes(b'replaced')
    assert c.post(route).status_code == 400
    assert c.get(link + '/video').status_code == 400
    assert c.get('/runtime/keys/signing.key').status_code == 404
    assert c.get('/api/status', headers={'host': 'attacker.example'}).status_code == 400


def test_report_api_limits_and_malformed(tmp_path):
    c, _ = client(tmp_path)
    assert c.post('/api/verify', files={'video': ('a', b'v'), 'report': ('b', b'{}')}).status_code == 400
    assert c.post('/api/verify', files={'video': ('a', b'v'), 'report': ('b', b'x' * 384001)}).status_code == 413
    assert c.post('/api/analyze', files={'video': ('a', b'')}).status_code == 400
    response = c.post('/api/analyze', content=b'x', headers={'content-length': str(102 * 1024 * 1024)})
    assert response.status_code == 413


def test_verify_route_displays_independent_checks(tmp_path):
    c, _ = client(tmp_path)
    envelope = upload(c)['envelope']
    result = c.post('/api/verify', files={'video': ('v', b'changed'),
                                         'report': ('r.json', json.dumps(envelope).encode())}).json()
    assert result['signature_valid'] is True and result['hash_matches'] is False
    assert result['signed_ai_assessment'] == 'Low detected manipulation risk'


def test_coverage_and_multiple_face_aggregation():
    s = Settings()
    assert aggregate([0.05, 0.95], 12, 12, 0, s)[0] == 'Suspicious'
    assert aggregate([0.05], 12, 12, 1, s)[0] == 'Inconclusive'
    assert aggregate([0.05], 2, 12, 0, s)[0] == 'Inconclusive'
    assert aggregate([], 0, 12, 0, s)[0] == 'Inconclusive'
    assert aggregate([0.05], 12, 12, 0, s)[0] == 'Low detected manipulation risk'
    assert aggregate([0.5], 12, 12, 0, s)[0] == 'Inconclusive'


def test_real_corrupt_upload_and_unavailable_model(tmp_path, monkeypatch):
    import cv2
    import numpy as np
    import app.detector as module
    from app.service import run_detector
    corrupt = tmp_path / 'broken.mp4'
    corrupt.write_bytes(b'corrupt video')
    result = run_detector(corrupt, Settings())
    assert result['assessment'] == 'Inconclusive' and not result['detector_available']
    app = create_app(tmp_path / 'web', Settings())
    c = TestClient(app); c.get('/')
    c.headers['x-csrf-token'] = c.get('/api/session').json()['csrf_token']
    item = upload(c, b'corrupt video')
    assert not item['report']['sharing_policy']['allowed']
    assert c.post('/api/reports/' + item['report']['report_id'] + '/share').status_code == 403
    video = tmp_path / 'valid.mp4'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'mp4v'), 5, (128, 128))
    for _ in range(10): writer.write(np.zeros((128, 128, 3), dtype=np.uint8))
    writer.release()
    monkeypatch.setattr(module, 'model_ready', lambda: (False, 'Detector unavailable / test'))
    result = analyze(video, Settings())
    assert result['assessment'] == 'Inconclusive' and result['score'] is None
    with pytest.raises(ValueError, match='duration'):
        analyze(video, replace(Settings(), max_duration_seconds=1))


def test_analysis_timeout_fails_closed(tmp_path, monkeypatch):
    import subprocess
    from app.service import run_detector
    def timeout(*args, **kwargs): raise subprocess.TimeoutExpired('worker', 1)
    monkeypatch.setattr(subprocess, 'run', timeout)
    assert not run_detector(tmp_path / 'x', Settings())['detector_available']


def test_unsigned_or_tampered_stored_report_cannot_share(tmp_path):
    c, service = client(tmp_path)
    item = upload(c)
    identifier = item['report']['report_id']
    item['report']['analysis']['reason'] = 'changed without signing'
    envelope = {**item['envelope'], 'payload': base64.b64encode(canonical(item['report'])).decode()}
    with service.db() as con:
        con.execute('UPDATE reports SET envelope=? WHERE id=?', (json.dumps(envelope), identifier))
    assert c.post(f'/api/reports/{identifier}/share').status_code == 400


def test_backend_coverage_recheck_and_busy_rejection(tmp_path):
    c, service = client(tmp_path)
    def insufficient(path, settings):
        result = detector()(path, settings)
        result['coverage']['rejected_faces'] = 1
        return result
    service.detector = insufficient
    item = upload(c)
    identifier = item['report']['report_id']
    assert not item['report']['sharing_policy']['allowed']
    assert c.post(f'/api/reports/{identifier}/share').status_code == 403
    service.lock.acquire()
    try:
        assert c.post('/api/analyze', files={'video': ('v', b'a')}).status_code == 429
    finally:
        service.lock.release()


def test_changed_during_analysis_not_signed(tmp_path):
    c, service = client(tmp_path)
    def replace_file(path, settings):
        path.write_bytes(b'changed during analysis')
        return detector()(path, settings)
    service.detector = replace_file
    assert c.post('/api/analyze', files={'video': ('v', b'original')}).status_code == 400
    assert c.get('/api/reports').json() == []
    assert list((service.root / 'videos').glob('*')) == []
