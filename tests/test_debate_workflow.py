"""Offline tests of new framework gate, explicit stages, and honest evidence table.
Synthetic URLs and quotations are fixtures, not verified public information.
"""
from __future__ import annotations
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock
from docx import Document
from tests.content_fixtures import MODEL_RESPONSE, write_sources
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills' / '一辩稿DOCX输出' / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('debate_workflow_offline', SCRIPTS / 'debate_workflow.py')
workflow = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = workflow
spec.loader.exec_module(workflow)

MOCK_CFG = {
    'default_provider': 'mock',
    'roles': {'research_synthesis': 'mock', 'drafting': 'mock', 'review': 'mock'},
    'providers': {'mock': {'protocol': 'openai_chat', 'model': 'test', 'api_key_env': 'TEST_UNUSED_KEY'}},
}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.products = self.root / 'products'
        self.framefile = self.root / '框架.txt'
        self.framefile.write_text('判准：保护事实的解释力。\n论点一：A。\n论点二：B。\n边界：不改辩题。', encoding='utf8')
        self.source_file = write_sources(self.root / 'content-sources.json')

    def execute(self, stage, *, extra=None, mocked=True):
        args = ['debate_workflow.py', '--stage', stage, '--topic', '认知/发展?', '--side', '正方',
                '--products-dir', str(self.products), '--content-sources-file', str(self.source_file)] + (extra or [])
        out = io.StringIO(); err = io.StringIO()
        router = Mock()
        router.generate.return_value = SimpleNamespace(
            text=MODEL_RESPONSE,
            provider='mock', model='test', response_id='offline')
        with patch.object(sys, 'argv', args), redirect_stdout(out), redirect_stderr(err):
            if mocked:
                with patch.object(workflow, 'load_config', return_value=MOCK_CFG), patch.object(workflow, 'ModelRouter', return_value=router):
                    code = workflow.main()
            else:
                code = workflow.main()
        return code, out.getvalue(), err.getvalue(), router

    def test_framework_first_gate_and_no_unrequested_outputs(self):
        code, stdout, stderr, router = self.execute('first')
        self.assertEqual(code, 2)
        self.assertIn('框架先行', stderr)
        self.assertFalse(self.products.exists())
        router.generate.assert_not_called()

        code, stdout, stderr, router = self.execute('framework', extra=['--framework-file', str(self.framefile)], mocked=False)
        self.assertEqual(code, 0, stderr)
        frame_docx = self.products / workflow.artifact_filename('认知/发展?', '正方', 'framework')
        self.assertTrue(frame_docx.exists())
        self.assertEqual(len(list(self.products.glob('*.docx'))), 1)
        self.assertIn('请先确认', stdout)
        self.assertNotIn(workflow.OFFER, stdout)
        self.assertIn('论点一', '\n'.join(p.text for p in Document(frame_docx).paragraphs))

    def test_first_invites_later_roles_but_does_not_generate_them(self):
        code, stdout, stderr, router = self.execute('first', extra=['--framework-file', str(self.framefile), '--duration', '3分钟'])
        self.assertEqual(code, 0, stderr)
        router.generate.assert_called_once()
        self.assertIn(workflow.OFFER, stdout)
        self.assertEqual(list(self.products.glob('*.docx'))[0].name, '认知-发展--正方-一辩稿.docx')
        self.assertEqual(len(list(self.products.glob('*.docx'))), 1)

    def test_user_requested_third_and_attack_stay_in_framework(self):
        code, stdout, stderr, router = self.execute('third', extra=['--framework-file', str(self.framefile)])
        self.assertEqual(code, 0, stderr)
        self.assertNotIn(workflow.OFFER, stdout)
        prompt = router.generate.call_args.kwargs['user_prompt']
        self.assertIn('判准：保护事实的解释力', prompt)
        self.assertIn('质询目标', prompt)
        self.assertTrue((self.products / '认知-发展--正方-三辩质询问题.docx').exists())

    def test_attack_document_contains_real_word_table_and_hyperlinks(self):
        evidence_file = self.root / 'evidence.json'
        evidence = {'evidence': [{
            'id': 'E1', 'claim': '用于示意的核验命题', 'quote': '测试用短引',
            'url': 'https://example.org/source', 'title': '测试来源', 'author': '测试单位',
            'date': '未标注日期', 'usage': '证明', 'limitation': '仅离线结构测试',
            'encounter': '假设对手追问研究条件', 'verified': True, 'quote_confirmed': True,
        }]}
        evidence_file.write_text(json.dumps(evidence, ensure_ascii=False), encoding='utf8')
        code, stdout, stderr, _ = self.execute('attack-defense', extra=['--framework-file', str(self.framefile), '--evidence-file', str(evidence_file)])
        self.assertEqual(code, 0, stderr)
        output = self.products / '认知-发展--正方-攻防稿.docx'
        doc = Document(output)
        self.assertEqual(len(doc.tables), 1)
        row = doc.tables[0].rows[2].cells
        self.assertEqual([cell.text for cell in doc.tables[0].rows[0].cells], ['可用资料摘要', '资料来源', '可核验链接'])
        self.assertIn('测试用短引', row[0].text)
        self.assertIn('测试单位', row[1].text)
        with zipfile.ZipFile(output) as z:
            xml = z.read('word/document.xml').decode('utf8')
            rels = z.read('word/_rels/document.xml.rels').decode('utf8')
            self.assertIn('w:hyperlink', xml)
            self.assertIn('https://example.org/source', rels)

    def test_unverified_excerpt_not_exported(self):
        path = self.root / 'invalid.json'
        path.write_text(json.dumps({'evidence': [{
            'id': 'E1', 'claim': '待查', 'quote': '来源未知', 'url': 'https://example.org/source',
            'title': '测试', 'author': '某人', 'date': '未知', 'usage': '防守', 'limitation': '未知',
            'encounter': '假设质询', 'verified': False, 'quote_confirmed': False
        }]}, ensure_ascii=False), encoding='utf8')
        code, _, stderr, router = self.execute('attack-defense', extra=['--framework-file', str(self.framefile), '--evidence-file', str(path)])
        self.assertEqual(code, 2)
        self.assertIn('人工核验', stderr)
        self.assertFalse(self.products.exists())
        router.generate.assert_not_called()

    def test_no_evidence_produces_candid_gap(self):
        code, stdout, stderr, _ = self.execute('attack-defense', extra=['--framework-file', str(self.framefile)])
        self.assertEqual(code, 0, stderr)
        doc = Document(self.products / '认知-发展--正方-攻防稿.docx')
        self.assertIn('待补', '\n'.join(p.text for p in doc.paragraphs))
        self.assertEqual(len(doc.tables), 0)

    def test_filename_rules_for_all_stages(self):
        for stage, suffix in workflow.ROLES.items():
            self.assertEqual(workflow.artifact_filename('诗/远方', '反方', stage), f'诗-远方-反方-{suffix}.docx')


if __name__ == '__main__':
    unittest.main()
