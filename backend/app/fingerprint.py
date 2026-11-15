"""Perceptual hashing and recompression-robust video fingerprinting.

Computes 64-bit DCT perceptual hashes across sampled video frames and provides
Hamming similarity comparisons to distinguish exact matches, re-encoded/compressed
content, and altered/tampered videos.
"""
import base64
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Union, Optional, Tuple, Dict, Any
import cv2
import numpy as np


def compute_phash(bgr: np.ndarray) -> str:
    """Compute a 64-bit DCT perceptual hash as a 16-character hex string.

    1. Convert frame to grayscale.
    2. Resize to 32x32.
    3. Compute 2D Discrete Cosine Transform (DCT).
    4. Extract the low-frequency 8x8 block.
    5. Compute median of AC coefficients (excluding DC term at 0,0).
    6. Threshold coefficients against median to produce 64 robust bits.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(np.float32(resized))
    low_freq = dct[:8, :8]
    # Median across AC coefficients to avoid DC illumination dominance
    median = float(np.median(low_freq[1:, 1:])) if low_freq.shape[0] > 1 else float(np.median(low_freq))
    bits = (low_freq > median).flatten()
    val = 0
    for b in bits:
        val = (val << 1) | int(b)
    return f'{val:016x}'


def hamming_distance(h1: str, h2: str) -> int:
    """Compute bitwise Hamming distance between two 16-hex perceptual hashes (0 to 64)."""
    try:
        v1 = int(h1, 16)
        v2 = int(h2, 16)
        return bin(v1 ^ v2).count('1')
    except (ValueError, TypeError):
        return 64


def compute_video_fingerprint(
    video_source: Union[Path, str, bytes],
    sample_frames: int = 12,
    max_pixels: int = 1920 * 1080
) -> Dict[str, Any]:
    """Extract sampled frame perceptual hashes from a video file path or raw bytes."""
    temp_file = None
    if isinstance(video_source, (bytes, bytearray)):
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4')
        with os.fdopen(temp_fd, 'wb') as stream:
            stream.write(video_source)
        video_path = Path(temp_path)
        temp_file = video_path
    else:
        video_path = Path(video_source)

    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {'version': 1, 'algorithm': 'dct_phash_64', 'sample_frames': 0, 'frames': []}

        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        if frames < 1 or not np.isfinite(fps) or fps <= 0:
            cap.release()
            return {'version': 1, 'algorithm': 'dct_phash_64', 'sample_frames': 0, 'frames': []}

        indices = np.unique(np.linspace(0, frames - 1, min(sample_frames, frames), dtype=int))
        frame_hashes = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, bgr = cap.read()
            if not ok or bgr is None:
                continue
            if bgr.shape[0] * bgr.shape[1] > max_pixels:
                continue
            h = compute_phash(bgr)
            frame_hashes.append({
                'frame': int(idx),
                'timestamp_seconds': round(float(idx / fps), 3),
                'phash': h
            })
        cap.release()
        return {
            'version': 1,
            'algorithm': 'dct_phash_64',
            'sample_frames': len(frame_hashes),
            'frames': frame_hashes
        }
    finally:
        if temp_file is not None and temp_file.exists():
            try:
                temp_file.unlink(missing_ok=True)
            except OSError:
                pass


def compare_fingerprints(
    fp1: Optional[Dict[str, Any]],
    fp2: Optional[Dict[str, Any]],
    max_bit_distance: int = 12,
    threshold: float = 0.82
) -> Dict[str, Any]:
    """Compare two perceptual fingerprints using temporal nearest-frame matching.

    Returns:
        similarity (float): Normalized score from 0.0 (unrelated) to 1.0 (identical visual structure).
        is_match (bool): True if similarity exceeds threshold.
        avg_bit_distance (float): Mean bit difference per matched frame.
        matched_frames (int): Frames where Hamming distance <= max_bit_distance.
        total_frames (int): Total frames evaluated.
    """
    if not fp1 or not fp2:
        return {
            'similarity': 0.0,
            'is_match': False,
            'avg_bit_distance': 64.0,
            'matched_frames': 0,
            'total_frames': 0,
            'threshold': threshold
        }

    f1 = fp1.get('frames', [])
    f2 = fp2.get('frames', [])
    if not f1 or not f2:
        return {
            'similarity': 0.0,
            'is_match': False,
            'avg_bit_distance': 64.0,
            'matched_frames': 0,
            'total_frames': 0,
            'threshold': threshold
        }

    distances = []
    matched = 0

    for item1 in f1:
        t1 = float(item1.get('timestamp_seconds', 0.0))
        h1 = item1.get('phash')
        if not h1:
            continue
        # Find closest temporal frame in second fingerprint
        closest = min(f2, key=lambda x: abs(float(x.get('timestamp_seconds', 0.0)) - t1))
        h2 = closest.get('phash')
        if not h2:
            continue
        d = hamming_distance(h1, h2)
        distances.append(d)
        if d <= max_bit_distance:
            matched += 1

    if not distances:
        return {
            'similarity': 0.0,
            'is_match': False,
            'avg_bit_distance': 64.0,
            'matched_frames': 0,
            'total_frames': 0,
            'threshold': threshold
        }

    avg_d = float(sum(distances)) / len(distances)
    similarity = max(0.0, min(1.0, 1.0 - (avg_d / 64.0)))

    return {
        'similarity': round(similarity, 4),
        'is_match': bool(similarity >= threshold),
        'avg_bit_distance': round(avg_d, 2),
        'matched_frames': matched,
        'total_frames': len(distances),
        'threshold': threshold
    }


def recompress_video(
    input_source: Union[Path, str, bytes],
    output_path: Optional[Path] = None,
    crf: int = 32,
    scale: Optional[float] = None
) -> bytes:
    """Recompress a video with high H.264 compression (simulating social media transcode).

    Uses ffmpeg if available, with a fallback to OpenCV VideoWriter.
    Returns the recompressed video bytes.
    """
    temp_in = None
    if isinstance(input_source, (bytes, bytearray)):
        fd, temp_in_path = tempfile.mkstemp(suffix='.mp4')
        with os.fdopen(fd, 'wb') as stream:
            stream.write(input_source)
        input_path = Path(temp_in_path)
        temp_in = input_path
    else:
        input_path = Path(input_source)

    temp_out = None
    if output_path is None:
        fd_out, temp_out_path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd_out)
        out_target = Path(temp_out_path)
        temp_out = out_target
    else:
        out_target = Path(output_path)

    ffmpeg_bin = shutil.which('ffmpeg')
    if ffmpeg_bin:
        vf_args = []
        if scale and 0.1 <= scale < 1.0:
            vf_args = ['-vf', f'scale=trunc(iw*{scale}/2)*2:trunc(ih*{scale}/2)*2']
        cmd = [
            ffmpeg_bin, '-y', '-i', str(input_path),
            *vf_args,
            '-c:v', 'libx264', '-crf', str(crf), '-preset', 'faster',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            str(out_target)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and out_target.exists() and out_target.stat().st_size > 0:
            data = out_target.read_bytes()
            if temp_in:
                temp_in.unlink(missing_ok=True)
            if temp_out:
                temp_out.unlink(missing_ok=True)
            return data

    # Fallback to OpenCV if ffmpeg fails
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        if temp_in:
            temp_in.unlink(missing_ok=True)
        if temp_out:
            temp_out.unlink(missing_ok=True)
        raise RuntimeError('Unable to open video for recompression')

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0 or not np.isfinite(fps):
        fps = 24.0

    target_w = int(width * (scale or 1.0))
    target_h = int(height * (scale or 1.0))
    # Dimensions must be even
    target_w -= target_w % 2
    target_h -= target_h % 2

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(out_target), fourcc, fps, (target_w, target_h))

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        if target_w != width or target_h != height:
            frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
        writer.write(frame)

    cap.release()
    writer.release()

    if out_target.exists() and out_target.stat().st_size > 0:
        data = out_target.read_bytes()
    else:
        data = b''

    if temp_in:
        temp_in.unlink(missing_ok=True)
    if temp_out:
        temp_out.unlink(missing_ok=True)
    return data
