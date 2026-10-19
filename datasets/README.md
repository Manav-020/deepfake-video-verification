# Attach legally obtained labeled videos here

No dataset is included. Create `datasets/validation/real`, `datasets/validation/fake`,
`datasets/test/real`, and `datasets/test/fake` (setup creates these empty directories).
Evaluation uses a CSV manifest so related identities/original videos can be grouped explicitly.

Create `datasets/manifest.csv` with:

```csv
path,label,split,group
validation/real/original_001.mp4,real,validation,identity_family_001
validation/fake/manipulated_001.mp4,fake,validation,identity_family_001
test/real/original_002.mp4,real,test,identity_family_002
test/fake/manipulated_002.mp4,fake,test,identity_family_002
```

Paths are relative to the manifest. Example names are placeholders, not provided videos.
Group related originals, derivatives, shared identities and source/target relationships together;
use connected identity families when multiple identities occur in a video. Groups cannot cross splits.
The evaluator rejects duplicate paths and cross-split identical bytes/groups. It cannot infer identity
relationships you omit. Do not split frames from one video across sets.

Request FaceForensics++ access at https://github.com/ondyari/FaceForensics under its terms.
Obtain original and manipulated videos (for example c23 originals and Deepfakes/FaceSwap/Face2Face/
NeuralTextures), associated labels/source relationships, and the official split metadata.
Prefer the official partition, then strengthen identity separation where possible and document changes.
Do not combine shared identities into both partitions merely to maintain an official video split.
Alternatively request Celeb-DF-v2 via https://github.com/yuezunli/celeb-deepfakeforensics;
use Celeb-real, YouTube-real and Celeb-synthesis videos plus its provided test-list metadata.
Follow the authors' access/license rules; no access control bypass is supplied.

For a bounded course experiment choose a balanced legal subset within 100 MB / 120 s / 1080p
per video and document selection. Decode-limit failures remain inconclusive, not deleted.
Both training datasets of a chosen detector and related source videos must be considered:
neither DFDC training data nor portraits repeated for smoke tests establish independent generalization.

Run validation first, choose thresholds using validation only, then freeze config.json and evaluate
the untouched test partition. See [the evaluation guide](../docs/EVALUATION.md) for the protocol and limitations.
