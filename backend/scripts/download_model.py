"""Download a pinned artifact; verify before atomic installation. Never execute remote Python."""
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT
from app.model_spec import REPO, REVISION, FILENAME, CHECKSUM, metadata


def main():
    folder = ROOT / 'models'
    folder.mkdir(exist_ok=True)
    target = folder / FILENAME
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == CHECKSUM:
        print('Checkpoint already verified:', CHECKSUM)
        return
    url = f'https://huggingface.co/{REPO}/resolve/{REVISION}/{FILENAME}'
    partial = folder / 'download.partial'
    print('Downloading pinned MIT DFDC checkpoint:', url, flush=True)
    try:
        with urllib.request.urlopen(url, timeout=90) as response, partial.open('wb') as out:
            size = 0
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > 600_000_000:
                    raise ValueError('Checkpoint exceeds download limit')
                out.write(chunk)
        if hashlib.sha256(partial.read_bytes()).hexdigest() != CHECKSUM:
            raise ValueError('Checkpoint checksum mismatch; refusing installation')
        # Preserve code for inspection without loading/executing the archive.
        with zipfile.ZipFile(partial) as archive:
            code = {n: archive.read(n).decode('utf-8') for n in archive.namelist()
                    if '/code/' in n and n.endswith('.py')}
        (folder / 'torchscript-code-review.json').write_text(json.dumps(code, indent=2))
        partial.replace(target)
        (folder / 'manifest.json').write_text(json.dumps(metadata(), indent=2))
        for filename in ('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
            urllib.request.urlretrieve(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{filename}',
                                       folder / filename)
        print('Verified SHA-256:', CHECKSUM, '\nInspect models/torchscript-code-review.json before first load.')
    finally:
        partial.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
