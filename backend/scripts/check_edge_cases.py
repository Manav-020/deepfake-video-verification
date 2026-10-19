"""Real face-pipeline integration checks. Generated fixtures are not evaluation videos."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT, load_settings
from app.service import run_detector


def main():
    import cv2
    import numpy as np
    folder = ROOT / 'artifacts'
    portrait = cv2.imread(str(folder / 'astronaut.png'))
    if portrait is None:
        raise SystemExit('Run scripts/smoke_model.py first')
    cases = {'no-faces': np.zeros_like(portrait), 'two-faces': np.concatenate([portrait, portrait], axis=1)}
    outputs = {}
    for name, frame in cases.items():
        path = folder / (name + '.mp4')
        h, w = frame.shape[:2]
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 3, (w, h))
        for _ in range(12): writer.write(frame)
        writer.release()
        result = run_detector(path, load_settings())
        assert result['detector_available'], result
        outputs[name] = result
    assert outputs['no-faces']['assessment'] == 'Inconclusive'
    assert outputs['no-faces']['coverage']['analyzed_faces'] == 0
    assert outputs['two-faces']['coverage']['analyzed_faces'] == 24
    for item in outputs['two-faces']['coverage']['frame_results']:
        assert len([f for f in item['faces'] if 'model_score' in f]) == 2
    (folder / 'edge-smoke.json').write_text(json.dumps(outputs, indent=2))
    print('REAL PIPELINE: no faces -> inconclusive; two faces -> both analyzed on all 12 sampled frames')


if __name__ == '__main__':
    main()
