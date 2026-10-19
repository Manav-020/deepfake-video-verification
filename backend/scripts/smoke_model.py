"""Real pipeline smoke on a public-domain portrait repeated as video. NOT evaluation data."""
import argparse
import json
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT, load_settings
from app.service import run_detector


def main():
    import cv2
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video', type=Path, help='Optional video you have rights to analyze')
    args = p.parse_args()
    artifacts = ROOT / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    video = args.video
    if video is None:
        portrait = artifacts / 'astronaut.png'
        if not portrait.exists():
            urllib.request.urlretrieve('https://raw.githubusercontent.com/scikit-image/scikit-image/v0.25.2/skimage/data/astronaut.png', portrait)
        frame = cv2.imread(str(portrait))
        video = artifacts / 'portrait-smoke.mp4'
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'mp4v'), 6, (512, 512))
        if not writer.isOpened():
            raise RuntimeError('MP4 fixture encoder unavailable')
        for _ in range(24):
            writer.write(frame)
        writer.release()
    result = run_detector(video.resolve(), load_settings())
    (artifacts / 'model-smoke.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if not result.get('detector_available') or not result.get('coverage', {}).get('analyzed_faces'):
        raise SystemExit('Real model smoke FAILED: no face inference completed')
    print('Real face inference completed. This fixture is NOT a labeled deepfake benchmark.')


if __name__ == '__main__':
    main()
