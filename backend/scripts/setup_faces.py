"""Extract ONLY data files from a SHA-256 pinned published MTCNN wheel."""
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT

URL = 'https://files.pythonhosted.org/packages/ed/2e/2d56386bc2f834cdc683743903852cf1428b4e5ee119f16cf808b589d3cd/facenet_pytorch-2.6.0-py3-none-any.whl'
SHA = 'ecb82b27beb226d106f2219efe8f829b01b87a8595badd01545679bdb9f19cca'


def main():
    from app._vendor.face_weights import HASHES
    target = ROOT / 'models/mtcnn'
    target.mkdir(exist_ok=True)
    if all((target / (n + '.pt')).exists() and hashlib.sha256((target / (n + '.pt')).read_bytes()).hexdigest() == h for n, h in HASHES.items()):
        print('MTCNN weights already verified')
        return
    with urllib.request.urlopen(URL, timeout=60) as response:
        blob = response.read(5_000_000)
    if hashlib.sha256(blob).hexdigest() != SHA:
        raise ValueError('Published MTCNN wheel hash mismatch')
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for name, checksum in HASHES.items():
            data = archive.read('facenet_pytorch/data/' + name + '.pt')
            if hashlib.sha256(data).hexdigest() != checksum:
                raise ValueError('MTCNN weight hash mismatch')
            (target / (name + '.pt')).write_bytes(data)
    print('Three MTCNN weights verified and installed; no downloaded Python executed')


if __name__ == '__main__':
    main()
