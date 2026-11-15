import base64
import json
import os
import tempfile
import cv2
import numpy as np
import pytest
from starlette.testclient import TestClient
from app.config import Settings
from app.crypto import Signer, verify
from app.fingerprint import (compute_phash, hamming_distance,
                             compute_video_fingerprint, compare_fingerprints,
                             recompress_video)
from app.main import create_app
from app.service import Service


def create_synthetic_video(path, num_frames=15, pattern='circle'):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(path), fourcc, 10.0, (160, 160))
    for i in range(num_frames):
        img = np.zeros((160, 160, 3), np.uint8)
        if pattern == 'circle':
            cv2.putText(img, f'Frame {i}', (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.circle(img, (80, 80), 30, (0, 200, 255), -1)
        else:
            cv2.rectangle(img, (20, 20), (140, 140), (255, 50, 50), -1)
            cv2.line(img, (0, 0), (160, 160), (0, 255, 0), 3)
        writer.write(img)
    writer.release()


def test_fingerprint_generation_and_comparison(tmp_path):
    vid1 = tmp_path / 'original.mp4'
    vid2 = tmp_path / 'altered.mp4'
    create_synthetic_video(vid1, num_frames=15, pattern='circle')
    create_synthetic_video(vid2, num_frames=15, pattern='rect')

    fp1 = compute_video_fingerprint(vid1)
    assert fp1['sample_frames'] > 0
    assert len(fp1['frames']) == fp1['sample_frames']

    # Recompress video 1
    recompressed_bytes = recompress_video(vid1, crf=32)
    assert len(recompressed_bytes) > 0
    fp_reencoded = compute_video_fingerprint(recompressed_bytes)

    # Recompressed should match fp1 with high similarity
    cmp_reencoded = compare_fingerprints(fp1, fp_reencoded)
    assert cmp_reencoded['is_match'] is True
    assert cmp_reencoded['similarity'] >= 0.85

    # Altered video should fail match
    fp2 = compute_video_fingerprint(vid2)
    cmp_diff = compare_fingerprints(fp1, fp2)
    assert cmp_diff['is_match'] is False
    assert cmp_diff['similarity'] < 0.75


def test_three_tier_verification_outcomes(tmp_path):
    # Setup test service
    signer = Signer(tmp_path / 'keys')
    vid_path = tmp_path / 'source.mp4'
    create_synthetic_video(vid_path, num_frames=15, pattern='circle')
    original_bytes = vid_path.read_bytes()

    fake_detector = lambda path, settings: {
        'assessment': 'Low detected manipulation risk',
        'score': 0.05,
        'detector_available': True,
        'coverage': {'analyzed_frames': 12, 'requested_frames': 12, 'analyzed_faces': 12, 'rejected_faces': 0},
        'perceptual_fingerprint': compute_video_fingerprint(vid_path)
    }

    service = Service(tmp_path, Settings(), fake_detector)
    res = service.finish('0123456789abcdef0123456789abcdef', 'owner', vid_path)
    envelope = res['envelope']

    # 1. Exact Match Check
    outcome_exact = verify(envelope, original_bytes, service.signer.registry)
    assert outcome_exact['signature_valid'] is True
    assert outcome_exact['hash_matches'] is True
    assert outcome_exact['content_matches'] is True
    assert outcome_exact['verification_outcome'] == 'exact_match'
    assert outcome_exact['social_media_ready'] is True

    # 2. Same Content, Re-encoded Check
    recompressed = recompress_video(vid_path, crf=30)
    assert recompressed != original_bytes
    outcome_reencoded = verify(envelope, recompressed, service.signer.registry)
    assert outcome_reencoded['signature_valid'] is True
    assert outcome_reencoded['hash_matches'] is False
    assert outcome_reencoded['content_matches'] is True
    assert outcome_reencoded['verification_outcome'] == 'reencoded_match'
    assert outcome_reencoded['fingerprint_similarity'] >= 0.85
    assert outcome_reencoded['social_media_ready'] is True

    # 3. Content Altered Check
    alt_path = tmp_path / 'alt.mp4'
    create_synthetic_video(alt_path, num_frames=15, pattern='rect')
    outcome_altered = verify(envelope, alt_path.read_bytes(), service.signer.registry)
    assert outcome_altered['signature_valid'] is True
    assert outcome_altered['hash_matches'] is False
    assert outcome_altered['content_matches'] is False
    assert outcome_altered['verification_outcome'] == 'content_altered'
    assert outcome_altered['social_media_ready'] is False


def test_social_media_guardrail_blocks_fake_even_when_recompressed(tmp_path):
    vid_path = tmp_path / 'fake.mp4'
    create_synthetic_video(vid_path, num_frames=15, pattern='circle')
    original_bytes = vid_path.read_bytes()

    fake_detector = lambda path, settings: {
        'assessment': 'Suspicious',
        'score': 0.95,
        'detector_available': True,
        'coverage': {'analyzed_frames': 12, 'requested_frames': 12, 'analyzed_faces': 12, 'rejected_faces': 0},
        'perceptual_fingerprint': compute_video_fingerprint(vid_path)
    }

    service = Service(tmp_path, Settings(), fake_detector)
    res = service.finish('fedcba9876543210fedcba9876543210', 'owner', vid_path)
    envelope = res['envelope']

    # Test exact match on fake video
    outcome_exact = verify(envelope, original_bytes, service.signer.registry)
    assert outcome_exact['social_media_ready'] is False
    assert 'NOT READY TO UPLOAD' in outcome_exact['social_media_reason']

    # Test recompressed fake video
    recompressed = recompress_video(vid_path, crf=32)
    outcome_reencoded = verify(envelope, recompressed, service.signer.registry)
    assert outcome_reencoded['verification_outcome'] == 'reencoded_match'
    assert outcome_reencoded['social_media_ready'] is False
    assert 'NOT READY TO UPLOAD' in outcome_reencoded['social_media_reason']


def test_demo_recompress_endpoint(tmp_path):
    vid_path = tmp_path / 'sample.mp4'
    create_synthetic_video(vid_path, num_frames=10, pattern='circle')

    app = create_app(runtime=tmp_path / 'rt')
    c = TestClient(app)
    c.get('/api/session')
    csrf = c.get('/api/session').json()['csrf_token']

    # Post video to recompress endpoint
    res = c.post(
        '/api/demo/recompress',
        headers={'x-csrf-token': csrf},
        files={'video': ('sample.mp4', vid_path.read_bytes(), 'video/mp4')},
        data={'crf': 32}
    )
    assert res.status_code == 200
    assert len(res.content) > 0
    assert res.headers['content-type'] == 'video/mp4'
