"""Video-level evaluation with explicit abstentions and split/leakage checks."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import load_settings
from app.model_spec import metadata
from app.service import run_detector


def load_manifest(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    if not rows or not {'path', 'label', 'split', 'group'} <= rows[0].keys():
        raise ValueError('CSV requires path,label,split,group and at least one video')
    seen_groups, seen_hashes, seen_paths = {}, {}, set()
    for row in rows:
        if row['label'] not in ('real', 'fake') or row['split'] not in ('validation', 'test') or not row['group'].strip():
            raise ValueError('Labels must be real/fake, splits validation/test, groups nonempty')
        video = (path.parent / row['path']).resolve()
        if video in seen_paths:
            raise ValueError('Duplicate video path in manifest')
        seen_paths.add(video)
        if not video.is_file():
            raise ValueError(f'Missing dataset video: {row["path"]}')
        with video.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        for value, seen in ((row['group'], seen_groups), (sha, seen_hashes)):
            if value in seen and seen[value] != row['split']:
                raise ValueError('Leakage: related group or identical video occurs across splits')
            seen[value] = row['split']
        row['resolved_path'] = video
    return rows


def metrics(records):
    from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
    decided = [r for r in records if r['assessment'] != 'Inconclusive']
    truth = [int(r['label'] == 'fake') for r in decided]
    pred = [int(r['assessment'] == 'Suspicious') for r in decided]
    scored = [r for r in records if r['score'] is not None]
    roc_truth = [int(r['label'] == 'fake') for r in scored]
    return {'video_count': len(records), 'decided_count': len(decided),
            'inconclusive_count': len(records) - len(decided),
            'inconclusive_rate': (len(records) - len(decided)) / len(records) if records else None,
            'inconclusive_by_label': {label: sum(r['assessment'] == 'Inconclusive' for r in records if r['label'] == label) for label in ('real', 'fake')},
            'precision': float(precision_score(truth, pred, zero_division=0)) if decided else None,
            'recall': float(recall_score(truth, pred, zero_division=0)) if decided else None,
            'f1': float(f1_score(truth, pred, zero_division=0)) if decided else None,
            'confusion_matrix': confusion_matrix(truth, pred, labels=[0, 1]).tolist() if decided else [[0, 0], [0, 0]],
            'confusion_matrix_order': 'rows actual [real,fake], columns predicted [real,fake]; decided videos only',
            'roc_auc': float(roc_auc_score(roc_truth, [r['score'] for r in scored])) if len(set(roc_truth)) == 2 else None,
            'roc_scored_count': len(scored),
            'inconclusive_handling': 'Excluded from precision/recall/F1/confusion matrix; all finite scored videos included in ROC-AUC, including abstentions. Null-score videos excluded from ROC. Report coverage and abstention rates alongside metrics; these conditional metrics can be optimistic.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--split', choices=['validation', 'test'], required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    rows = [r for r in load_manifest(args.manifest) if r['split'] == args.split]
    if not rows:
        p.error('No videos in the selected split; attach labeled data first')
    settings = load_settings()
    records = []
    for i, row in enumerate(rows):
        print(f'[{i+1}/{len(rows)}] {row["path"]}', flush=True)
        video = row['resolved_path']
        if video.stat().st_size > settings.max_upload_mb * 1024 * 1024:
            result = {'assessment': 'Inconclusive', 'score': None, 'reason': 'Upload size limit'}
        else:
            result = run_detector(video, settings)
        records.append({'path': row['path'], 'label': row['label'], 'group': row['group'], **result})
    output = {'evaluated_at': datetime.now(timezone.utc).isoformat(), 'split': args.split,
              'model': metadata(), 'settings': settings.dict(), 'metrics': metrics(records), 'videos': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(output['metrics'], indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
