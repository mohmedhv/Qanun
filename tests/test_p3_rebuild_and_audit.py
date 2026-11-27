"""Additional P3 reproducibility and legal provenance tests."""
import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.versions.audit_amendments import audit
from src.versions.rebuild_db import rebuild
from src.versions.versions import rank_conflict


class RebuildAndAuditTests(unittest.TestCase):
    def test_unknown_legal_rank_is_not_misclassified_as_equal(self):
        result = rank_conflict('unidentified-norm-000', 'loi')
        self.assertEqual(result['winner'], 'undetermined')
        self.assertEqual(result['rule'], 'unknown_legal_rank')
        self.assertIsNone(result['prevailing_text'])

    def test_clean_rebuild_has_expected_schema_data_and_repeal(self):
        with tempfile.TemporaryDirectory() as td:
            db = rebuild(Path(td) / 'fresh.db')
            con=sqlite3.connect(db)
            self.assertEqual(con.execute('select count(*) from articles').fetchone()[0],158)
            self.assertEqual(con.execute('select count(*) from texts').fetchone()[0],11)
            self.assertEqual(con.execute('select count(*) from relations').fetchone()[0],89)
            seed = json.loads((Path(__file__).resolve().parents[1] / 'data/version_seed/p3_seed.json').read_text(encoding='utf-8'))
            self.assertEqual(con.execute('select count(*) from versions').fetchone()[0], len(seed['versions']))
            self.assertEqual(con.execute('select count(*) from versions where article_number = ? and valid_to IS NULL',('72',)).fetchone()[0],0)
            self.assertEqual(con.execute('select count(*) from versions where article_number = ? and valid_to IS NULL',('87 bis',)).fetchone()[0],0)
            con.close()

    def test_audit_has_79_entries_with_visible_pending(self):
        result = audit()
        self.assertEqual(len(result),79)
        self.assertEqual(sum(x['needs_review'] for x in result),0)
        self.assertEqual(sum(x['official_full_wording_checked'] for x in result),19)
        self.assertTrue(all(x['source_reference_url'] for x in result))
        self.assertEqual(len([x for x in result if x['modifying_text']=='loi-17-11']),14)


if __name__=='__main__':
    unittest.main()
