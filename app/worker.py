"""A disposable process gives decoding and CPU inference a hard wall-clock budget."""
import json
import sys
from pathlib import Path
from .config import Settings
from .detector import analyze

if __name__ == '__main__':
    try:
        result = analyze(Path(sys.argv[1]), Settings(**json.loads(sys.argv[2])))
        print(json.dumps({'ok': True, 'result': result}, allow_nan=False))
    except Exception as exc:
        # Only error categories reach the UI; paths and backend details remain private.
        message = str(exc) if isinstance(exc, (ValueError, TimeoutError)) else 'Detector inference failed'
        print(json.dumps({'ok': False, 'error': message}))
