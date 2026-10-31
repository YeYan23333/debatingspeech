"""Portable corpus assets and retrieval remain traceable and unverified."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills' / '一辩稿DOCX输出' / 'scripts'))
import retrieve_corpus


class CorpusTests(unittest.TestCase):
    def test_every_asset_matches_manifest_and_remains_unverified(self):
        corpus = ROOT / 'references' / 'corpus'
        records = json.loads((corpus / 'index.json').read_text(encoding='utf-8'))['documents']
        self.assertTrue(records)
        self.assertEqual(len({x['id'] for x in records}), len(records))
        for item in records:
            with self.subTest(id=item['id']):
                original = (corpus / item['original']).resolve()
                text = (corpus / item['text']).resolve()
                self.assertTrue(original.is_relative_to(corpus.resolve()))
                self.assertTrue(text.is_relative_to(corpus.resolve()))
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), item['sha256'])
                self.assertTrue(text.read_text(encoding='utf-8').strip())
                self.assertEqual(item['fact_verification'], 'unverified_user_material')
                self.assertNotIn('~$', item['filename'])

    def test_queries_use_actual_topic_and_do_not_return_unrelated_samples(self):
        result = retrieve_corpus.retrieve('念念不忘必有回响是中华文化特有的孤独', limit=2)
        self.assertTrue(result)
        self.assertTrue(any(x['id'] in ('U007', 'U008') for x in result))
        self.assertTrue(all(x['fact_verification'] == 'unverified_user_material' for x in result))
        self.assertEqual(retrieve_corpus.retrieve('城市地下水污染治理工程'), [])

    def test_index_cannot_read_outside_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'corpus'
            root.mkdir()
            outside = Path(tmp) / 'outside.md'
            outside.write_text('不得读取', encoding='utf-8')
            (root / 'index.json').write_text(json.dumps({'documents': [
                {'id': 'T1', 'filename': '崩溃行为研究', 'topic': '崩溃行为研究',
                 'text': '../outside.md'}]}), encoding='utf-8')
            with self.assertRaises(ValueError):
                retrieve_corpus.retrieve('崩溃行为研究', root=root)


if __name__ == '__main__': unittest.main()
