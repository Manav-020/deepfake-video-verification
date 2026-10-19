import hashlib
from pathlib import Path

HASHES = {
    'pnet': 'a2a71925e0b9996a42f63e47efc1ca19043e69558b5c523b978d611dfae49c8f',
    'rnet': 'bbb937de72efc9ef83b186c49f5f558467a1d7e3453a8ece0d71a886633f6a86',
    'onet': '165bfbe42940416ccfb977545cf0e976d5bf321f67083ae2aaaa5c764280118d',
}


def load_face_weights(name):
    import torch
    path = Path(__file__).resolve().parents[2] / 'models/mtcnn' / (name + '.pt')
    if hashlib.sha256(path.read_bytes()).hexdigest() != HASHES[name]:
        raise ValueError('MTCNN checkpoint checksum mismatch; run scripts/setup_faces.py')
    return torch.load(path, map_location='cpu', weights_only=True)
