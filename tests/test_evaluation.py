import csv
import pytest
from scripts.evaluate import metrics, load_manifest


def test_abstention_metrics():
    records = [{'label': 'real', 'assessment': 'Low detected manipulation risk', 'score': .1},
               {'label': 'fake', 'assessment': 'Suspicious', 'score': .9},
               {'label': 'fake', 'assessment': 'Inconclusive', 'score': .5},
               {'label': 'real', 'assessment': 'Inconclusive', 'score': None}]
    m = metrics(records)
    assert m['precision'] == m['recall'] == m['f1'] == m['roc_auc'] == 1.0
    assert m['confusion_matrix'] == [[1, 0], [0, 1]]
    assert m['inconclusive_rate'] == .5 and m['roc_scored_count'] == 3
    assert metrics([])['roc_auc'] is None


def test_manifest_detects_leakage(tmp_path):
    (tmp_path / 'one.mp4').write_bytes(b'one')
    (tmp_path / 'two.mp4').write_bytes(b'two')
    path = tmp_path / 'manifest.csv'
    path.write_text('path,label,split,group\none.mp4,real,validation,same-person\ntwo.mp4,fake,test,same-person\n')
    with pytest.raises(ValueError, match='Leakage'):
        load_manifest(path)
    path.write_text('path,label,split,group\none.mp4,real,validation,person1\ntwo.mp4,fake,test,person2\n')
    assert len(load_manifest(path)) == 2
