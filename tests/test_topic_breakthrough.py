"""Offline routing checks; the sample framework contains no verified public facts.

These tests check that the rules reach the model and old frameworks survive import.
They do not score the quality of model-generated topic analysis.
"""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docx import Document
from tests.test_docx_output import generator
from tests.test_debate_workflow import workflow, MOCK_CFG
from tests.content_fixtures import MODEL_RESPONSE, write_sources
from content_requirements import REQUIREMENTS_PROMPT


TOPIC = '测试流程甲应不应该继续采用'
OLD_FRAMEWORK = '判准：可纠正的执行成本。\n论点一：发现问题。\n论点二：降低修正代价。'
FRAMEWORK = (OLD_FRAMEWORK + '\n\n## 破题帮助\n'
             '测试用路线：比较继续执行与暂停后改进，哪一种安排更容易发现并纠正错误。\n'
             '主路线以错误发现与修正成本作为两条论点的分工；实际现象与学理来源均待补。')


class TopicGuidePromptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.breakthrough = self.root / 'breakthrough.md'
        self.quality = self.root / 'quality.md'

    def prompt(self, stage):
        if stage == 'legacy':
            return generator.make_prompts(TOPIC, '正方', '3分钟', FRAMEWORK, '')
        return workflow.prompt_for_stage(stage, TOPIC, '正方', '3分钟', FRAMEWORK, '', [], '')

    def test_all_stages_and_legacy_read_updated_guides_before_the_output_protocol(self):
        for stage in ('legacy', *workflow.ROLES):
            loader = generator.load_argument_quality_guides if stage == 'legacy' else workflow.load_argument_quality_guides
            with self.subTest(stage=stage), patch.dict(loader.__globals__, {
                'BREAKTHROUGH_GUIDE_PATH': self.breakthrough,
                'ARGUMENT_QUALITY_GUIDE_PATH': self.quality,
            }):
                self.breakthrough.write_text('TOPIC_REVISION_A：核对比较基线。', encoding='utf8')
                self.quality.write_text('ROLE_REVISION_A：按本辩位推进证明。', encoding='utf8')
                first, _ = self.prompt(stage)
                self.breakthrough.write_text('TOPIC_REVISION_B：选定真实分歧。', encoding='utf8')
                self.quality.write_text('ROLE_REVISION_B：保留同一判准。', encoding='utf8')
                second, _ = self.prompt(stage)
                for prefix in ('TOPIC', 'ROLE'):
                    self.assertIn(prefix + '_REVISION_A', first)
                    self.assertNotIn(prefix + '_REVISION_A', second)
                    self.assertIn(prefix + '_REVISION_B', second)
                if stage != 'framework':
                    self.assertTrue(second.endswith(REQUIREMENTS_PROMPT))
                    self.assertLess(second.index('TOPIC_REVISION_B'), second.index(REQUIREMENTS_PROMPT))
                    self.assertLess(second.index('ROLE_REVISION_B'), second.index(REQUIREMENTS_PROMPT))
                if stage == 'fourth':
                    self.assertLess(second.index('ROLE_REVISION_B'), second.index(workflow.load_closing_guide()))

    def test_missing_or_empty_required_guide_is_reported(self):
        for stage in ('legacy', 'framework', 'first'):
            loader = generator.load_argument_quality_guides if stage == 'legacy' else workflow.load_argument_quality_guides
            with self.subTest(stage=stage), patch.dict(loader.__globals__, {
                'BREAKTHROUGH_GUIDE_PATH': self.breakthrough,
                'ARGUMENT_QUALITY_GUIDE_PATH': self.quality,
            }):
                self.breakthrough.unlink(missing_ok=True)
                self.quality.write_text('测试用辩位规则', encoding='utf8')
                with self.assertRaises(OSError):
                    self.prompt(stage)
                self.breakthrough.write_text(' \n', encoding='utf8')
                with self.assertRaises(ValueError):
                    self.prompt(stage)

    def test_framework_task_requests_topic_specific_choices_and_role_tasks_keep_the_route(self):
        _, framework_prompt = self.prompt('framework')
        for concept in ('破题帮助', '真实分歧', '举证责任', '比较基线', '现象与学理', '推荐主路线', '最强挑战'):
            self.assertIn(concept, framework_prompt)
        self.assertIn('不硬凑数量', framework_prompt)
        for stage in workflow.ROLES:
            if stage == 'framework':
                continue
            _, prompt = self.prompt(stage)
            self.assertIn(FRAMEWORK, prompt)
            self.assertIn('不擅自换路线', prompt)
        _, missing = workflow.prompt_for_stage('first', TOPIC, '正方', '3分钟', OLD_FRAMEWORK, '', [], '')
        self.assertIn('破题帮助仍待补', missing)
        self.assertIn(OLD_FRAMEWORK, missing)


class TopicFrameworkCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.products = self.root / 'products'
        self.sources = write_sources(self.root / 'sources.json')

    def execute(self, *, stage='framework', imported=None, response=FRAMEWORK):
        args = ['debate_workflow.py', '--stage', stage, '--topic', TOPIC, '--side', '正方',
                '--products-dir', str(self.products), '--content-sources-file', str(self.sources)]
        if imported is not None:
            path = self.root / 'framework.md'
            path.write_text(imported, encoding='utf8')
            args += ['--framework-file', str(path)]
        router = Mock()
        router.generate.return_value = SimpleNamespace(text=response, provider='offline', model='test')
        out, err = io.StringIO(), io.StringIO()
        with (patch.object(sys, 'argv', args), patch.object(workflow, 'load_config', return_value=MOCK_CFG) as config,
              patch.object(workflow, 'ModelRouter', return_value=router) as factory,
              redirect_stdout(out), redirect_stderr(err)):
            code = workflow.main()
        return code, out.getvalue(), err.getvalue(), router, config, factory

    def test_importing_old_framework_keeps_original_and_appends_an_honest_gap_without_api(self):
        code, stdout, stderr, router, config, factory = self.execute(imported=OLD_FRAMEWORK)
        self.assertEqual(code, 0, stderr)
        router.generate.assert_not_called()
        config.assert_not_called()
        factory.assert_not_called()
        output = next(self.products.glob('*.docx'))
        text = '\n'.join(p.text for p in Document(output).paragraphs)
        self.assertIn(OLD_FRAMEWORK, text)
        self.assertIn('破题帮助（待补）', text)
        self.assertIn('尚未补出本题的实际切入点', text)
        self.assertIn('未调用模型', stdout)
        self.assertEqual(workflow.framework_breakthrough_status(text), 'pending')
        again, pending = workflow.preserve_imported_framework(text)
        self.assertEqual(again, text)
        self.assertTrue(pending)

    def test_complete_import_is_unchanged_and_generated_framework_needs_the_section(self):
        imported, pending = workflow.preserve_imported_framework(FRAMEWORK)
        self.assertEqual(imported, FRAMEWORK)
        self.assertFalse(pending)
        code, _, stderr, router, _, _ = self.execute(response=OLD_FRAMEWORK)
        self.assertEqual(code, 2)
        self.assertIn('缺少', stderr)
        self.assertIn('破题帮助', stderr)
        router.generate.assert_called_once()
        self.assertFalse(self.products.exists())
        code, stdout, stderr, router, _, _ = self.execute()
        self.assertEqual(code, 0, stderr)
        router.generate.assert_called_once()
        self.assertEqual(len(list(self.products.glob('*.docx'))), 1)
        text = '\n'.join(p.text for p in Document(next(self.products.glob('*.docx'))).paragraphs)
        for line in FRAMEWORK.splitlines():
            if line.strip():
                self.assertIn(line.removeprefix('## '), text)
        self.assertIn('不判断其论证质量', stdout)

    def test_pending_marker_is_not_accepted_as_completed_model_analysis(self):
        code, _, stderr, router, _, _ = self.execute(response=OLD_FRAMEWORK + '\n' + workflow.BREAKTHROUGH_PENDING)
        self.assertEqual(code, 2)
        self.assertIn('仍标为待补', stderr)
        router.generate.assert_called_once()
        self.assertFalse(self.products.exists())

    def test_section_detection_accepts_user_formats_without_treating_evidence_gaps_as_no_route(self):
        for text in ('## **二、破题帮助**\n测试路线：比较可纠错成本。',
                     '破题帮助：测试路线比较可纠错成本，学理来源待补。',
                     '{"判准":"测试判准","破题帮助":"测试核心路线，现象出处待补"}'):
            with self.subTest(text=text):
                preserved, pending = workflow.preserve_imported_framework(text)
                self.assertEqual(preserved, text)
                self.assertFalse(pending)
        self.assertEqual(workflow.framework_breakthrough_status('请在后面增加破题帮助。'), 'missing')
        self.assertEqual(workflow.framework_breakthrough_status('{"破题帮助":"待补"}'), 'pending')
        self.assertEqual(workflow.framework_breakthrough_status('【破题帮助】（待补）'), 'pending')

    def test_all_manuscript_stages_keep_one_call_and_content_gate(self):
        for stage in workflow.ROLES:
            if stage == 'framework':
                continue
            with self.subTest(stage=stage):
                code, _, stderr, router, _, _ = self.execute(stage=stage, imported=FRAMEWORK, response=MODEL_RESPONSE)
                self.assertEqual(code, 0, stderr)
                router.generate.assert_called_once()
                self.assertTrue(router.generate.call_args.kwargs['system_prompt'].endswith(REQUIREMENTS_PROMPT))
        self.assertEqual(len(list(self.products.glob('*.docx'))), len(workflow.ROLES) - 1)
        # Changing a model response after valid sources must still stop before DOCX export.
        with patch.object(workflow, 'artifact_filename', return_value='invalid-body.docx'):
            code, _, stderr, router, _, _ = self.execute(stage='first', imported=FRAMEWORK, response='没有现象、学理与来源绑定的测试文本')
        self.assertEqual(code, 2)
        router.generate.assert_called_once()
        self.assertFalse((self.products / 'invalid-body.docx').exists())


if __name__ == '__main__':
    unittest.main()
