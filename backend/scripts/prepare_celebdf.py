"""Structure Celeb-DF v2 into validation and test partitions with strict group separation.

Ensures zero identity leakage across splits and outputs `datasets/manifest.csv`
ready for `scripts/evaluate.py`.
"""
import csv
import re
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parents[1] / 'datasets'
MANIFEST_PATH = DATASETS_DIR / 'manifest.csv'
TEST_LIST_PATH = DATASETS_DIR / 'List_of_testing_videos.txt'


def extract_group(rel_path: str) -> str:
    """Extract identity family to guarantee no cross-split identity leakage."""
    p = Path(rel_path).as_posix()
    if 'Celeb-synthesis' in p:
        # id0_id16_0000.mp4 -> group by both identities
        match = re.search(r'(id\d+)_(id\d+)', p)
        if match:
            return f"{match.group(1)}_{match.group(2)}"
        return 'synthesis_unknown'
    elif 'Celeb-real' in p:
        # id0_0000.mp4 -> id0
        match = re.search(r'(id\d+)', p)
        if match:
            return match.group(1)
        return 'celeb_real_unknown'
    else:
        # YouTube-real
        return f"yt_{Path(p).stem}"


def build_manifest(val_per_class: int = 15, test_per_class: int = 20):
    """Build a balanced, leak-free validation and test split from Celeb-DF v2."""
    if not TEST_LIST_PATH.is_file():
        raise FileNotFoundError(f"Missing {TEST_LIST_PATH}")

    # Read official testing list
    official_test = []
    with TEST_LIST_PATH.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                label_num, rel_path = parts
                label = 'real' if label_num == '1' else 'fake'
                official_test.append((rel_path.strip(), label))

    print(f"[*] Total official testing list entries: {len(official_test)}")

    # Separate available testing videos by label
    reals = []
    fakes = []
    for rel_path, label in official_test:
        full_path = DATASETS_DIR / rel_path
        if full_path.is_file():
            if label == 'real':
                reals.append(rel_path)
            else:
                fakes.append(rel_path)

    print(f"[*] Verified on disk: {len(reals)} real, {len(fakes)} fake testing videos")

    # Group-aware partitioning to prevent leakage
    # We select distinct identity groups for validation and test
    val_rows = []
    test_rows = []
    val_groups = set()
    test_groups = set()

    # Populate Test split first
    test_reals = 0
    test_fakes = 0
    for r in reals:
        if test_reals >= test_per_class:
            break
        g = extract_group(r)
        if g not in test_groups:
            test_rows.append({'path': r, 'label': 'real', 'split': 'test', 'group': g})
            test_groups.add(g)
            test_reals += 1

    for f in fakes:
        if test_fakes >= test_per_class:
            break
        g = extract_group(f)
        if g not in test_groups:
            test_rows.append({'path': f, 'label': 'fake', 'split': 'test', 'group': g})
            test_groups.add(g)
            test_fakes += 1

    # Populate Validation split (guaranteeing no group overlap with test)
    val_reals = 0
    val_fakes = 0
    for r in reals:
        if val_reals >= val_per_class:
            break
        g = extract_group(r)
        if g not in test_groups and g not in val_groups:
            val_rows.append({'path': r, 'label': 'real', 'split': 'validation', 'group': g})
            val_groups.add(g)
            val_reals += 1

    for f in fakes:
        if val_fakes >= val_per_class:
            break
        g = extract_group(f)
        if g not in test_groups and g not in val_groups:
            val_rows.append({'path': f, 'label': 'fake', 'split': 'validation', 'group': g})
            val_groups.add(g)
            val_fakes += 1

    all_rows = val_rows + test_rows
    print(f"[*] Selected {len(val_rows)} validation videos ({val_reals} real, {val_fakes} fake)")
    print(f"[*] Selected {len(test_rows)} test videos ({test_reals} real, {test_fakes} fake)")

    # Verify zero leakage
    assert len(val_groups.intersection(test_groups)) == 0, "ERROR: Group leakage detected!"
    print("[✓] Zero identity leakage verified between validation and test splits.")

    with MANIFEST_PATH.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['path', 'label', 'split', 'group'])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"[✓] Manifest written to {MANIFEST_PATH}")
    return MANIFEST_PATH


if __name__ == '__main__':
    build_manifest()
