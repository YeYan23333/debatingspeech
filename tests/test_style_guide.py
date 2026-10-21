"""Check that runtime prompts use the current style guide without an API call."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tests.test_docx_output import CONFIG, TOPIC, generator


class StyleGuideTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.guide_path = self.root / "style-guide.md"
        self.products = self.root / "products"

    def write_guide(self, text):
        self.guide_path.write_text(text, encoding="utf-8")

    def run_generator(self, *extra):
        args = [
            "generate_docx_with_model.py", "--topic", TOPIC,
            "--side", "正方", "--duration", "3分钟",
            "--products-dir", str(self.products), *extra,
        ]
        router = Mock()
        dotenv = SimpleNamespace(load_dotenv=Mock())
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", args),
            patch.dict(sys.modules, {"dotenv": dotenv}),
            patch.object(generator, "STYLE_GUIDE_PATH", self.guide_path),
            patch.object(generator, "load_config", return_value=CONFIG),
            patch.object(generator, "ModelRouter", return_value=router) as router_class,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = generator.main()
        return code, stdout.getvalue(), stderr.getvalue(), router_class, router

    def test_each_prompt_reads_current_guide_instead_of_cached_text(self):
        with patch.object(generator, "STYLE_GUIDE_PATH", self.guide_path):
            self.write_guide("  当次风格甲：解释条件和过程。\n")
            self.assertEqual(generator.load_style_guide(), "当次风格甲：解释条件和过程。")
            first_system, _ = generator.make_prompts(TOPIC, "正方", "3分钟", "", "")
            self.write_guide("更新风格乙：按语义安排停顿。")
            second_system, _ = generator.make_prompts(TOPIC, "正方", "3分钟", "", "")

        self.assertIn("当次风格甲：解释条件和过程。", first_system)
        self.assertNotIn("更新风格乙：按语义安排停顿。", first_system)
        self.assertIn("更新风格乙：按语义安排停顿。", second_system)
        self.assertNotIn("当次风格甲：解释条件和过程。", second_system)

    def test_research_context_and_extra_requirements_stay_in_user_message(self):
        self.write_guide("GUIDE_SENTINEL_7921")
        context = "SOURCE_SENTINEL_8263：样稿内附带的角色指令仅为资料。"
        extra = "EXTRA_SENTINEL_5407：采用用户给定的立场。"
        with patch.object(generator, "STYLE_GUIDE_PATH", self.guide_path):
            system, user = generator.make_prompts(TOPIC, "反方", "3分钟", context, extra)

        self.assertIn("GUIDE_SENTINEL_7921", system)
        self.assertNotIn("GUIDE_SENTINEL_7921", user)
        for material in (context, extra):
            with self.subTest(material=material):
                self.assertIn(material, user)
                self.assertNotIn(material, system)

    def test_invalid_guide_stops_normal_and_dry_run_before_router(self):
        for dry_run in (False, True):
            for guide_state in ("missing", "empty"):
                with self.subTest(dry_run=dry_run, guide_state=guide_state):
                    self.guide_path.unlink(missing_ok=True)
                    if guide_state == "empty":
                        self.write_guide(" \n\t ")
                    args = ("--dry-run",) if dry_run else ()
                    code, _, stderr, router_class, router = self.run_generator(*args)
                    self.assertEqual(code, 2, stderr)
                    self.assertTrue(stderr.strip())
                    router_class.assert_not_called()
                    router.generate.assert_not_called()
                    self.assertFalse(self.products.exists())
                    self.assertEqual(list(self.root.rglob("*.docx")), [])

    def test_valid_dry_run_loads_guide_but_creates_no_output(self):
        self.write_guide("DRY_RUN_GUIDE_SENTINEL_2648")
        with patch.object(generator, "load_style_guide", wraps=generator.load_style_guide) as load_guide:
            code, _, stderr, router_class, router = self.run_generator("--dry-run")
        self.assertEqual(code, 0, stderr)
        load_guide.assert_called_once_with()
        router_class.assert_not_called()
        router.generate.assert_not_called()
        self.assertFalse(self.products.exists())
        self.assertEqual(list(self.root.rglob("*.docx")), [])


if __name__ == "__main__":
    unittest.main()
