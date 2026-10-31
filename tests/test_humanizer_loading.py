"""Check both prompt builders load current local editing rules without API calls."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.test_docx_output import generator
from tests.test_debate_workflow import workflow
from content_requirements import REQUIREMENTS_PROMPT


class HumanizerLoadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guide = Path(self.tmp.name) / 'SKILL.md'

    def builders(self):
        return (
            ('legacy', generator.load_humanizer_guide,
             lambda: generator.make_prompts('学习方式', '正方', '3分钟', '', '')[0]),
            ('workflow', workflow.load_humanizer_guide,
             lambda: workflow.prompt_for_stage('first', '学习方式', '正方', '3分钟', '已确认框架', '', [], '')[0]),
        )

    def test_both_entry_points_read_each_current_local_revision_before_hard_protocol(self):
        # Change a real temporary guide between calls. This catches cached text,
        # an unused loader, and putting upstream output requirements after the
        # source-bound final-output protocol without testing particular prose.
        for name, loader, build in self.builders():
            with self.subTest(entry=name), patch.dict(loader.__globals__, {'HUMANIZER_GUIDE_PATH': self.guide}):
                self.guide.write_text('HUMANIZER_REVISION_A：修改冗余表述。', encoding='utf8')
                first = build()
                self.guide.write_text('HUMANIZER_REVISION_B：变化句长并保留引用。', encoding='utf8')
                second = build()
                self.assertIn('HUMANIZER_REVISION_A', first)
                self.assertNotIn('HUMANIZER_REVISION_B', first)
                self.assertIn('HUMANIZER_REVISION_B', second)
                self.assertNotIn('HUMANIZER_REVISION_A', second)
                self.assertLess(second.index('HUMANIZER_REVISION_B'), second.index(REQUIREMENTS_PROMPT))
                self.assertTrue(second.endswith(REQUIREMENTS_PROMPT))

    def test_missing_optional_local_guide_keeps_existing_generation_protocol(self):
        for name, loader, build in self.builders():
            with self.subTest(entry=name), patch.dict(loader.__globals__, {'HUMANIZER_GUIDE_PATH': self.guide}):
                self.assertEqual(loader(), '')
                self.assertIn(REQUIREMENTS_PROMPT, build())

    def test_present_but_empty_local_guide_is_reported_instead_of_claimed_loaded(self):
        self.guide.write_text(' \n\t', encoding='utf8')
        for name, loader, build in self.builders():
            with self.subTest(entry=name), patch.dict(loader.__globals__, {'HUMANIZER_GUIDE_PATH': self.guide}):
                with self.assertRaises(ValueError):
                    build()


if __name__ == '__main__':
    unittest.main()
