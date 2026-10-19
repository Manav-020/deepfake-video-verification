"""Export public trust information only, for deliberate out-of-band trust establishment."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT

if __name__ == '__main__':
    path = ROOT / 'runtime/keys/trusted_keys.json'
    if not path.is_file():
        raise SystemExit('Launch the app once to initialize its signing key and registry')
    print(json.dumps(json.loads(path.read_text()), indent=2))
