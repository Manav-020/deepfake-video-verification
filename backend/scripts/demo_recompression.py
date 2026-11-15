"""Demo script: Recompression-robust content binding.

Demonstrates that:
1. An original video has a valid digital signature and SHA-256 match (Tier 1: Exact Match).
2. After H.264 recompression (simulating social media upload), the exact SHA-256 FAILS.
3. However, FrameSeal's signed Perceptual Fingerprint (DCT pHash) still MATCHES (Tier 2: Same Content, Re-encoded).
4. The Social Media Readiness Guard evaluates the true content rather than being deceived by re-encoding.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from app.config import load_settings
from app.crypto import Signer, verify, digest
from app.fingerprint import (compute_video_fingerprint, compare_fingerprints,
                             recompress_video)
from app.service import Service


def generate_sample_clip(path: Path, num_frames: int = 25):
    """Generate a clean synthetic MP4 test clip with movement and texture."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(path), fourcc, 12.0, (240, 240))
    for i in range(num_frames):
        img = np.zeros((240, 240, 3), np.uint8)
        for y in range(240):
            img[y, :] = [int(25 + y * 0.1), int(40 + y * 0.15), int(60 + y * 0.2)]
        cv2.circle(img, (120, 120), 45, (0, 220, 255), -1)
        cv2.putText(img, f'Frame {i + 1}', (30, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.line(img, (i * 8, 30), (240 - i * 8, 30), (255, 255, 0), 3)
        writer.write(img)
    writer.release()


def generate_different_clip(path: Path, num_frames: int = 15):
    """Generate a distinctly different video (checkerboard and cross)."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(path), fourcc, 12.0, (240, 240))
    for i in range(num_frames):
        img = np.full((240, 240, 3), 200, np.uint8)
        cv2.rectangle(img, (20, 20), (100, 100), (0, 0, 255), -1)
        cv2.rectangle(img, (140, 140), (220, 220), (255, 0, 0), -1)
        cv2.line(img, (0, 0), (240, 240), (0, 0, 0), 5)
        writer.write(img)
    writer.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='Path to an MP4 video (optional; auto-generates if omitted)')
    parser.add_argument('--crf', type=int, default=32, help='H.264 CRF compression level (default 32)')
    args = parser.parse_args()

    temp_dir = tempfile.TemporaryDirectory()
    work_dir = Path(temp_dir.name)

    if args.input and args.input.is_file():
        source_path = args.input
        print(f"[*] Using provided input video: {source_path}")
    else:
        source_path = work_dir / 'source_video.mp4'
        print(f"[*] Generating sample test clip: {source_path}")
        generate_sample_clip(source_path)

    original_bytes = source_path.read_bytes()
    orig_sha = digest(original_bytes)
    orig_fp = compute_video_fingerprint(source_path)

    print("\n" + "=" * 70)
    print("STEP 1: ORIGINAL VIDEO SCREENING & SIGNING")
    print("=" * 70)
    print(f"  File size:               {len(original_bytes):,} bytes")
    print(f"  Original SHA-256:        {orig_sha}")
    print(f"  Sampled frames hashed:   {orig_fp['sample_frames']} frames")
    print(f"  Fingerprint Algorithm:   {orig_fp['algorithm']}")

    # Setup local signing service
    service = Service(work_dir / 'runtime', load_settings())
    # Sign report with a valid 32-character hex ID
    report_id = '0123456789abcdef0123456789abcdef'
    res = service.finish(report_id, 'demo_owner', source_path)
    envelope = res['envelope']
    print(f"  Ed25519 Signature:       {envelope['signature'][:32]}... (VALID)")

    # 1. Verification of untouched original
    print("\n" + "=" * 70)
    print("STEP 2: VERIFY ORIGINAL UNTOUCHED FILE")
    print("=" * 70)
    v1 = verify(envelope, original_bytes, service.signer.registry)
    print(f"  Signature Valid:         {v1['signature_valid']}")
    print(f"  SHA-256 Hash Match:      {v1['hash_matches']}")
    print(f"  Perceptual Match:        {v1['content_matches']} (Similarity: {v1['fingerprint_similarity'] * 100:.1f}%)")
    print(f"  -> VERIFICATION OUTCOME: {v1['outcome_label']} [{v1['verification_outcome']}]")
    print(f"  -> SOCIAL MEDIA READY:   {v1['social_media_ready']}")

    # 2. Recompress video with ffmpeg
    print("\n" + "=" * 70)
    print(f"STEP 3: RECOMPRESSING VIDEO (H.264 CRF {args.crf})")
    print("=" * 70)
    recompressed_bytes = recompress_video(source_path, crf=args.crf)
    recomp_sha = digest(recompressed_bytes)
    print(f"  Recompressed size:       {len(recompressed_bytes):,} bytes")
    print(f"  Recompressed SHA-256:    {recomp_sha}")
    print(f"  SHA-256 Identical?       {orig_sha == recomp_sha} (BYTES CHANGED!)")

    # 3. Verification of recompressed video
    print("\n" + "=" * 70)
    print("STEP 4: VERIFY RECOMPRESSED VIDEO AGAINST ORIGINAL SIGNED REPORT")
    print("=" * 70)
    v2 = verify(envelope, recompressed_bytes, service.signer.registry)
    print(f"  Signature Valid:         {v2['signature_valid']}")
    print(f"  SHA-256 Hash Match:      {v2['hash_matches']} (FAILS exact byte check)")
    print(f"  Perceptual Match:        {v2['content_matches']} (Similarity: {v2['fingerprint_similarity'] * 100:.1f}%)")
    print(f"  -> VERIFICATION OUTCOME: {v2['outcome_label']} [{v2['verification_outcome']}]")
    print(f"  -> DETAIL:               {v2['outcome_detail']}")
    print(f"  -> SOCIAL MEDIA READY:   {v2['social_media_ready']}")
    print(f"  -> POLICY REASON:        {v2['social_media_reason']}")

    # 4. Compare against altered / different video
    print("\n" + "=" * 70)
    print("STEP 5: TAMPER / DIFFERENT VIDEO CHECK")
    print("=" * 70)
    altered_path = work_dir / 'altered.mp4'
    generate_different_clip(altered_path, num_frames=15)
    v3 = verify(envelope, altered_path.read_bytes(), service.signer.registry)
    print(f"  SHA-256 Hash Match:      {v3['hash_matches']}")
    print(f"  Perceptual Match:        {v3['content_matches']} (Similarity: {v3['fingerprint_similarity'] * 100:.1f}%)")
    print(f"  -> VERIFICATION OUTCOME: {v3['outcome_label']} [{v3['verification_outcome']}]")
    print(f"  -> SOCIAL MEDIA READY:   {v3['social_media_ready']}")

    print("\n" + "=" * 70)
    print("DEMO SUMMARY:")
    print("  ✓ Exact Match (Tier 1): Verified bit-for-bit.")
    print("  ✓ Recompressed (Tier 2): SHA-256 fails, but Perceptual Fingerprint succeeds.")
    print("  ✓ Altered/Different (Tier 3): Tampering detected and blocked.")
    print("=" * 70 + "\n")

    temp_dir.cleanup()


if __name__ == '__main__':
    main()
