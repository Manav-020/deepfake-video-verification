import json
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    max_upload_mb: int = 100
    max_duration_seconds: int = 120
    sample_frames: int = 12
    max_faces_per_frame: int = 8
    min_face_pixels: int = 64
    min_face_confidence: float = 0.9
    min_analyzed_frames: int = 4
    min_coverage: float = 0.75
    low_threshold: float = 0.2
    suspicious_threshold: float = 0.8
    analysis_timeout_seconds: int = 180
    max_pixels: int = 2073600
    torch_threads: int = 4

    def __post_init__(self):
        if not 0 <= self.low_threshold < self.suspicious_threshold <= 1:
            raise ValueError('Thresholds must satisfy 0 <= low < suspicious <= 1')
        if not 0 < self.min_coverage <= 1 or not 0 < self.min_face_confidence <= 1:
            raise ValueError('Coverage/confidence outside (0, 1]')
        for name in ('max_upload_mb', 'max_duration_seconds', 'sample_frames',
                     'max_faces_per_frame', 'min_face_pixels', 'min_analyzed_frames',
                     'analysis_timeout_seconds', 'max_pixels', 'torch_threads'):
            if not isinstance(getattr(self, name), int) or getattr(self, name) < 1:
                raise ValueError(f'{name} must be a positive integer')
        if self.sample_frames > 64 or self.max_faces_per_frame > 16:
            raise ValueError('Sampling exceeds safety ceiling')

    def dict(self):
        return asdict(self)


def load_settings():
    path = ROOT / 'config.json'
    return Settings(**json.loads(path.read_text())) if path.exists() else Settings()
