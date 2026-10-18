# User actions required

Last updated: 2026-10-18.

The local application and real detector are installed and work. No cloud account, paid API, training,
or model-access approval is required to run it. The following work needs your identity/data access.

## 1. Authenticate GitHub and publish the private repository

**Why:** GitHub CLI is available locally, but `gh auth status` reports no authenticated GitHub hosts.
I cannot choose/sign into your account. Git identity was already configured and was preserved.
No GitHub repository was created; no remote exists; no push has succeeded.

**Exact commands** (from this project):

```powershell
Set-Location -LiteralPath 'D:\coding\python\ISC Project'
.\tools\gh\gh.exe auth login --hostname github.com --git-protocol https --web
.\tools\gh\gh.exe auth status
.\tools\gh\gh.exe repo create deepfake-video-verification --private --source . --remote origin --push
.\tools\gh\gh.exe repo view --json url,isPrivate
git remote -v
git ls-remote origin refs/heads/main
git rev-parse HEAD
```

**Expected destination:** a new private repository in the account you authenticate, with source under
`main`; `origin` is added only if absent. The descriptive name has not been reserved. If already taken,
choose an available new name such as `deepfake-video-verification-isc` in the `repo create` command.
Do not overwrite an existing remote or force-push. If a remote now exists, inspect it before proceeding.

**Verify completion:** `isPrivate` must be true; record the returned URL. Remote main’s hash must match
`git rev-parse HEAD`. Update PROJECT_STATUS.md with the verified URL/push status, commit that documentation
and `git push`. All local keys, videos, model weights, datasets, tools and virtual environment are ignored.
Do not paste credentials into this project or conversation. You can authenticate, then ask the agent to
finish creation/push and update the status if you prefer.

## 2. Obtain labeled videos for measured evaluation and a deepfake demonstration

**Why:** no real/fake dataset is attached. Integration smoke fixtures cannot establish detection quality,
choose validated thresholds, or demonstrate correct classification of actual deepfakes.

**Exact links:** request FaceForensics++ from its
[official Access section](https://github.com/ondyari/FaceForensics#access), or Celeb-DF-v2 from the
[authors’ repository](https://github.com/yuezunli/celeb-deepfakeforensics). Complete their access forms,
follow terms, and use only authorized download links. No request was submitted on your behalf.

**Required files/destination:** originals plus corresponding manipulated videos, labels, source/identity
relationships and official split metadata. Store a documented legal subset in:

```text
D:\coding\python\ISC Project\datasets\validation\real\
D:\coding\python\ISC Project\datasets\validation\fake\
D:\coding\python\ISC Project\datasets\test\real\
D:\coding\python\ISC Project\datasets\test\fake\
D:\coding\python\ISC Project\datasets\manifest.csv
```

The empty directories already exist. Create the manifest using datasets/README.md; separate related
videos/identities across partitions and retain dataset terms/metadata locally. Do not commit the videos.

**Commands/verification:**

```powershell
.\.venv\Scripts\python.exe scripts\evaluate.py --manifest datasets\manifest.csv --split validation --output artifacts\validation.json
# Select and freeze config.json on validation only.
.\.venv\Scripts\python.exe scripts\evaluate.py --manifest datasets\manifest.csv --split test --output artifacts\test.json
```

Both runs must contain the intended real/fake videos, report meaningful coverage and inconclusive rates,
and pass group/duplicate leakage checks. Inspect per-video failures rather than hiding them. Record
measured results and protocol in MODEL_AND_DATA.md and PROJECT_STATUS.md afterward. Existing UI warnings
must remain experimental unless evidence justifies a carefully documented change.

## Optional: establish trust on a second installation

**Why:** a different installation does not automatically trust this service’s signing key.
Export only public keys using `.\.venv\Scripts\python.exe scripts\export_public_keys.py`, exchange
through an authenticated channel, and deliberately add the verified entry to the recipient’s
`runtime/keys/trusted_keys.json`, preserving their own active key. Restart and verify an unchanged report
and matching file. Never trust a key merely because an uploaded report supplies it. See SECURITY_DESIGN.md.
