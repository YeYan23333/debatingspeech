"""Offline behavior tests of source-bound minimum-content checks, not fact checking."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.content_fixtures import SOURCES, model_payload, write_sources
from tests.test_debate_workflow import workflow, MOCK_CFG
from tests.test_docx_output import generator
from content_requirements import load_content_sources, validate_manuscript


class MinimumContentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source_file = write_sources(self.root / 'sources.json')
        self.sources = load_content_sources(str(self.source_file))
        self.frame_file = self.root / 'frame.txt'
        self.frame_file.write_text('判准：学习过程的改善。论点一：反馈。论点二：修正。', encoding='utf8')
        self.products = self.root / 'products'

    def run_cli(self, module, payload, *, sources=True):
        args = ['generate.py', '--topic', '学习方式', '--side', '正方', '--duration', '3分钟',
                '--products-dir', str(self.products)]
        if module is workflow:
            args += ['--stage', 'first', '--framework-file', str(self.frame_file)]
        if sources:
            args += ['--content-sources-file', str(self.source_file)]
        response = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        router = Mock()
        router.generate.return_value = SimpleNamespace(text=response, provider='mock', model='test', response_id='offline')
        out, err = io.StringIO(), io.StringIO()
        with (patch.object(sys, 'argv', args), patch.object(module, 'load_config', return_value=MOCK_CFG),
              patch.object(module, 'ModelRouter', return_value=router),
              patch.object(module, 'build_docx', wraps=module.build_docx) as build,
              redirect_stdout(out), redirect_stderr(err)):
            code = module.main()
        return code, err.getvalue(), router, build

    def test_both_clis_stop_before_export_when_a_required_kind_is_missing(self):
        for module in (workflow, generator):
            for missing in ('phenomenon', 'theory'):
                with self.subTest(cli=module.__name__, missing=missing):
                    payload = model_payload()
                    del payload['requirements'][missing]
                    code, err, router, build = self.run_cli(module, payload)
                    self.assertEqual(code, 2, err)
                    router.generate.assert_called_once()
                    build.assert_not_called()
                    self.assertFalse(self.products.exists())

    def test_both_clis_require_operator_sources_before_model_call(self):
        for module in (workflow, generator):
            with self.subTest(cli=module.__name__):
                code, err, router, build = self.run_cli(module, model_payload(), sources=False)
                self.assertEqual(code, 2, err)
                self.assertIn('--content-sources-file', err)
                router.generate.assert_not_called()
                build.assert_not_called()
                self.assertFalse(self.products.exists())

    def test_checks_cannot_add_content_that_is_absent_from_body(self):
        for kind in ('phenomenon', 'theory'):
            payload = model_payload()
            payload['body'] = payload['body'].replace(payload['requirements'][kind]['excerpt'], '')
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, '逐字出现在正文'):
                validate_manuscript(json.dumps(payload), self.sources)

    def test_appendix_or_reference_list_cannot_satisfy_minimum(self):
        for heading in ('## 参考文献', '附录', '## 待核验事项'):
            payload = model_payload()
            payload['body'] = '正文还没有材料。\n\n' + heading + '\n' + payload['body']
            with self.subTest(heading=heading), self.assertRaisesRegex(ValueError, '不能充抵'):
                validate_manuscript(json.dumps(payload), self.sources)

    def test_a_name_or_duplicated_label_does_not_satisfy_both_kinds(self):
        payload = model_payload()
        payload['requirements']['theory']['excerpt'] = '理论[1]'
        payload['body'] += '\n理论[1]'
        with self.assertRaisesRegex(ValueError, '名称或术语'):
            validate_manuscript(json.dumps(payload), self.sources)
        payload = model_payload()
        payload['requirements']['theory'] = deepcopy(payload['requirements']['phenomenon'])
        with self.assertRaisesRegex(ValueError, '同一段摘录'):
            validate_manuscript(json.dumps(payload), self.sources)

    def test_model_cannot_self_certify_or_introduce_unknown_sources(self):
        payload = model_payload()
        payload['references'] = [{'id': '99', 'verified': True}]
        payload['requirements']['theory']['source_ids'] = ['99']
        payload['requirements']['theory']['excerpt'] += '[99]'
        payload['body'] += '\n' + payload['requirements']['theory']['excerpt']
        with self.assertRaisesRegex(ValueError, '已核验登记'):
            validate_manuscript(json.dumps(payload), self.sources)
        registered = deepcopy(SOURCES)
        registered['sources'][0]['verified'] = False
        self.source_file.write_text(json.dumps(registered), encoding='utf8')
        with self.assertRaisesRegex(ValueError, '尚未由操作者确认核验'):
            load_content_sources(str(self.source_file))

    def test_source_kind_and_inline_marker_must_match(self):
        sources = deepcopy(self.sources)
        sources['1']['kind'] = 'phenomenon'
        with self.assertRaisesRegex(ValueError, '缺少已人工核验的学理'):
            validate_manuscript(json.dumps(model_payload()), sources)
        payload = model_payload()
        payload['requirements']['theory']['excerpt'] = payload['requirements']['theory']['excerpt'].replace('[1]', '')
        with self.assertRaisesRegex(ValueError, '绑定其来源'):
            validate_manuscript(json.dumps(payload), self.sources)

    def test_text_is_rejected_instead_of_silently_bypassing_structure(self):
        for module in (workflow, generator):
            with self.subTest(cli=module.__name__):
                code, err, _, build = self.run_cli(module, '一个现象，一个学理。')
                self.assertEqual(code, 2, err)
                self.assertIn('JSON', err)
                build.assert_not_called()

    def test_valid_output_uses_operator_bibliography_and_excludes_check_metadata(self):
        text = validate_manuscript(json.dumps(model_payload()), self.sources)
        self.assertIn('## 参考文献', text)
        self.assertIn('https://example.org/research?year=2026', text)
        self.assertNotIn('requirements', text)
        self.assertNotIn('verification_note', text)


if __name__ == '__main__':
    unittest.main()
