# Vendored MTCNN

`mtcnn.py` and `detect_face.py` originate from timesler/facenet-pytorch 2.6.0,
MIT licensed; copyright and license preserved in FACENET_LICENSE.md.
Source: https://github.com/timesler/facenet-pytorch and pinned PyPI wheel
SHA-256 `ecb82b27beb226d106f2219efe8f829b01b87a8595badd01545679bdb9f19cca`.

Changes: trailing whitespace normalization; local import location; three model weight loads delegate to face_weights.py
for pinned checksum verification, project-local paths and `weights_only=True`.
No detector algorithm changes. The unused extraction helpers remain upstream code.
Only MTCNN is used; recognition/identity embeddings are never calculated.

Reason: upstream metadata requires old Torch/Pillow/NumPy combinations without Python 3.13 wheels.
These two standalone modules run against the project's current tested CPU stack without installing
or bypassing the package's dependency constraints. Weights are downloaded separately and never committed.
