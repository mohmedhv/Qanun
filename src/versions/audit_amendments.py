"""Generate a transparent source/provenance ledger for the 79 P3 amendment entries.

This script checks internal integrity and assigns traceable source links.
It does NOT claim that every individual transcription has received an independent
human comparison with the official journal. Full-wording review flags and source checks are recorded independently.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if not __package__:
    sys.path.insert(0, str(ROOT))
DATA = ROOT / 'data/interim/amendments.json'
OUTPUT = ROOT / 'data/interim/amendment_audit.csv'

def audit():
    entries = json.loads(DATA.read_text(encoding='utf-8'))
    if len(entries) != 79:
        raise ValueError(f'Expected 79 P3 entries, found {len(entries)}; investigate before submission.')
    required = ['target_article', 'action', 'modifying_text_id', 'jo_date', 'amending_article']
    previous = {}
    if OUTPUT.exists():
        with OUTPUT.open('r', encoding='utf-8-sig', newline='') as f:
            previous = {(r['modifying_text'],r['article'],r['amending_article']): r for r in csv.DictReader(f)}
    from src.versions.load_versions import verification_rows
    official = {(r["modifying_text_id"], r["target_article"], r["provision"]): r
                for r in verification_rows()}
    ledger = []
    for i, row in enumerate(entries, 1):
        missing = [key for key in required if not str(row.get(key) or '').strip()]
        partial = bool(row.get('partial'))
        pending = bool(row.get('needs_review'))
        if missing:
            status = 'invalid_metadata'
        elif pending:
            status = 'needs_textual_review'
        else:
            status = 'source_checked'
        key = row["modifying_text_id"], row["target_article"], row["amending_article"]
        source = official[key]
        last = previous.get(key, {})
        ledger.append({
            'verification_status': source['verification_status'],
            'source_csv_row': source['csv_row'],
            'source_page': source['source_page'],
            'entry': i,
            'article': row.get('target_article',''),
            'action': row.get('action',''),
            'modifying_text': row['modifying_text_id'],
            'amending_article': row.get('amending_article',''),
            'official_journal_date': row.get('jo_date',''),
            'source_reference_url': source['source_url'],
            'source_trace': source['verification_note'],
            'official_full_wording_checked': bool(row.get('official_full_wording_checked', False)),
            'independent_check_status': 'pending' if not last.get('second_reviewer') else 'reviewer_recorded',
            'partial_amendment': partial,
            'needs_review': pending,
            'audit_status': status,
            'review_reason': row.get('review_reasons',''),
            'second_reviewer': last.get('second_reviewer', ''),
            'second_review_date': last.get('second_review_date', ''),
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(ledger[0]))
        writer.writeheader();writer.writerows(ledger)
    counts = Counter(r['audit_status'] for r in ledger)
    print('P3 inventory audit:',len(ledger),'entries;',dict(counts))
    print('Ledger:',OUTPUT)
    return ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict',action='store_true',help='Return nonzero if a source is unchecked or metadata are invalid')
    args=parser.parse_args()
    rows=audit()
    if args.strict and any(r['verification_status'] == 'a_verifier' or r['audit_status'] == 'invalid_metadata' for r in rows):
        raise SystemExit('P3 SOURCE AUDIT INCOMPLETE: check flagged sources and metadata.')


if __name__=='__main__':
    main()
