"""Real DFDC facial-forgery screening. No placeholder inference."""
import hashlib
import base64
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from .config import ROOT, Settings
from .model_spec import CHECKSUM


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def model_ready():
    path = ROOT / 'models/model.pt'
    if not path.is_file():
        return False, 'Detector unavailable: run scripts/download_model.py'
    checksum = _sha256_file(path)
    if checksum == CHECKSUM:
        from ._vendor.face_weights import HASHES
        for name, expected in HASHES.items():
            weight = ROOT / 'models/mtcnn' / (name + '.pt')
            if not weight.is_file() or hashlib.sha256(weight.read_bytes()).hexdigest() != expected:
                return False, 'Detector unavailable: run scripts/setup_faces.py to restore MTCNN weights'
    return (True, 'Checkpoint checksum verified; CPU inference') if checksum == CHECKSUM else (
        False, 'Detector unavailable: checkpoint checksum mismatch')


def aggregate(scores, covered_frames, requested_frames, rejected, settings):
    score = max(scores) if scores else None
    sufficient = (covered_frames >= settings.min_analyzed_frames
                  and covered_frames / requested_frames >= settings.min_coverage
                  and rejected == 0)
    if score is not None and score >= settings.suspicious_threshold:
        return 'Suspicious', score, 'At least one analyzed face exceeded the suspicious threshold'
    if sufficient and score is not None and score <= settings.low_threshold:
        return 'Low detected manipulation risk', score, 'All analyzed faces below provisional low threshold'
    return 'Inconclusive', score, 'Insufficient coverage/face quality or intermediate model score'


def _frame_preview(bgr, frame_result):
    """Encode the exact decoded sample with detector boxes; never part of signed report."""
    height, width = bgr.shape[:2]
    scale = min(1.0, 640 / width)
    image = cv2.resize(bgr, (round(width * scale), round(height * scale)),
                       interpolation=cv2.INTER_AREA) if scale < 1 else bgr.copy()
    for index, face in enumerate(frame_result['faces']):
        x1, y1, x2, y2 = [round(value * scale) for value in face['box']]
        color = (70, 224, 66) if face.get('model_score') is not None else (68, 180, 255)
        label = (f"Face {index + 1}: {face['model_score']:.3f}"
                 if face.get('model_score') is not None else f'Face {index + 1}: excluded')
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
        label_x = min(max(0, x1), max(0, image.shape[1] - text_width - 8))
        label_y = max(text_height + baseline + 4, y1)
        cv2.rectangle(image, (label_x, label_y - text_height - baseline - 4),
                      (label_x + text_width + 8, label_y + baseline), color, -1)
        cv2.putText(image, label, (label_x + 4, label_y - 2), cv2.FONT_HERSHEY_SIMPLEX,
                    0.48, (16, 37, 29), 1, cv2.LINE_AA)
    ok, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 76])
    if not ok:
        return None
    return {
        'frame': frame_result['frame'],
        'timestamp_seconds': frame_result['timestamp_seconds'],
        'faces': frame_result['faces'],
        'image': 'data:image/jpeg;base64,' + base64.b64encode(encoded).decode('ascii'),
    }


def analyze(path: Path, settings: Settings):
    cap = cv2.VideoCapture(str(path))
    try:
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        width, height = int(cap.get(3)), int(cap.get(4))
        if not cap.isOpened() or frames < 1 or not np.isfinite(fps) or fps <= 0:
            raise ValueError('Cannot decode video or determine duration; try a standard MP4 codec')
        duration = frames / fps
        if duration > settings.max_duration_seconds:
            raise ValueError('Video exceeds configured duration limit')
        if width < 1 or height < 1 or width * height > settings.max_pixels:
            raise ValueError('Video dimensions exceed configured limit')
        ok, first = cap.read()
        if not ok or first is None:
            raise ValueError('Video contains no decodable frames')
        result = {'assessment': 'Inconclusive', 'score': None, 'reason': '',
                  'detector_available': False, 'coverage': {'duration_seconds': duration,
                  'total_frames': frames, 'fps': fps, 'sampled_frames': 0,
                  'analyzed_frames': 0, 'analyzed_faces': 0, 'rejected_faces': 0,
                  'frame_results': []}}
        ready, reason = model_ready()
        if not ready:
            result['reason'] = reason
            return result
        import torch
        from ._vendor.mtcnn import MTCNN
        torch.set_num_threads(settings.torch_threads)
        model = torch.jit.load(str(ROOT / 'models/model.pt'), map_location='cpu').eval()
        faces = MTCNN(keep_all=True, thresholds=[0.7, 0.8, 0.8], device='cpu')
        mean = torch.tensor([0.485, 0.456, 0.406])[:, None, None]
        std = torch.tensor([0.229, 0.224, 0.225])[:, None, None]
        scores, covered, rejected = [], 0, 0
        previews = []
        indices = np.unique(np.linspace(0, frames - 1, min(settings.sample_frames, frames), dtype=int))
        started = time.monotonic()
        with torch.inference_mode():
            for idx in indices:
                if time.monotonic() - started > settings.analysis_timeout_seconds - 5:
                    raise TimeoutError('Analysis time budget exceeded')
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ok, bgr = cap.read()
                item = {'frame': int(idx), 'timestamp_seconds': float(idx / fps),
                        'faces': [], 'decoded': bool(ok)}
                result['coverage']['frame_results'].append(item)
                if not ok or bgr is None:
                    continue
                if bgr.shape[0] * bgr.shape[1] > settings.max_pixels:
                    raise ValueError('Decoded dimensions exceed limit')
                result['coverage']['sampled_frames'] += 1
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                # Upstream detects at half resolution, with no geometric alignment.
                image = Image.fromarray(rgb).resize((rgb.shape[1] // 2, rgb.shape[0] // 2))
                boxes, confidences = faces.detect(image)
                if boxes is None:
                    preview = _frame_preview(bgr, item)
                    if preview:
                        previews.append(preview)
                    continue
                frame_scores = []
                for j, (box, confidence) in enumerate(zip(boxes, confidences)):
                    x1, y1, x2, y2 = [int(v * 2) for v in box]
                    w, h = x2 - x1, y2 - y1
                    record = {'box': [x1, y1, x2, y2], 'face_confidence': float(confidence)}
                    item['faces'].append(record)
                    if (j >= settings.max_faces_per_frame or min(w, h) < settings.min_face_pixels
                            or confidence < settings.min_face_confidence):
                        rejected += 1
                        record['rejected'] = 'Face count, size or confidence limit'
                        continue
                    crop = rgb[max(0, y1 - h // 3):min(rgb.shape[0], y2 + h // 3),
                               max(0, x1 - w // 3):min(rgb.shape[1], x2 + w // 3)]
                    if crop.size == 0:
                        rejected += 1
                        record['rejected'] = 'Invalid crop'
                        continue
                    ch, cw = crop.shape[:2]
                    ratio = 380 / max(ch, cw)
                    resized = cv2.resize(crop, (max(1, int(cw * ratio)), max(1, int(ch * ratio))),
                                         interpolation=cv2.INTER_CUBIC if ratio > 1 else cv2.INTER_AREA)
                    canvas = np.zeros((380, 380, 3), np.uint8)
                    rh, rw = resized.shape[:2]
                    sy, sx = (380 - rh) // 2, (380 - rw) // 2
                    canvas[sy:sy + rh, sx:sx + rw] = resized
                    tensor = torch.from_numpy(canvas).permute(2, 0, 1).float() / 255
                    score = float(torch.sigmoid(model(((tensor - mean) / std)[None])).item())
                    if not np.isfinite(score):
                        raise ValueError('Model returned a nonfinite score')
                    record['model_score'] = score
                    frame_scores.append(score)
                    scores.append(score)
                if frame_scores:
                    covered += 1
                preview = _frame_preview(bgr, item)
                if preview:
                    previews.append(preview)
        assessment, score, reason = aggregate(scores, covered, len(indices), rejected, settings)
        result.update(assessment=assessment, score=score, reason=reason, detector_available=True)
        result['coverage'].update(analyzed_frames=covered, analyzed_faces=len(scores),
                                  rejected_faces=rejected, requested_frames=len(indices))
        result['previews'] = previews
        return result
    finally:
        cap.release()
