"""Exercise both DOCX entry points without API calls or private configuration."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docx import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PROJECT_ROOT / "skills" / "一辩稿DOCX输出" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The model script imports its sibling exporter, just as it does when run as a CLI.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
exporter = load_script("export_to_docx")
generator = load_script("generate_docx_with_model")

TOPIC = "AI 2.0：是否会改变 2026 年的学习方式？"
DRAFT = """# AI 2.0 与学习方式｜正方一辩稿

## 正文
主席、评委、各位同学，大家好。我方认为应该重视学习方式的变化。
当反馈更及时，学习者就能更快发现问题；这一判断需要结合具体条件理解。[1]

## 参考文献
[1] 示例资料（2026），https://example.org/research?year=2026
"""
CONFIG = {
    "default_provider": "offline_test",
    "roles": {"drafting": "offline_test"},
    "providers": {
        "offline_test": {
            "protocol": "openai_chat",
            "model": "offline-model",
            "api_key_env": "UNUSED_TEST_API_KEY",
        }
    },
}


class SpeechFilenameTests(unittest.TestCase):
    def test_uses_full_user_topic_preserving_legal_punctuation_and_spaces(self):
        for side in ("正方", "反方"):
            with self.subTest(side=side):
                self.assertEqual(
                    exporter.speech_filename(f"  {TOPIC}  ", side),
                    f"{TOPIC}-{side}-一辩稿.docx",
                )

    def test_replaces_windows_invalid_characters_and_control_characters(self):
        topic = '  教育/科技\\发展:比较<>"|?*\x00\x01\x1f尾部...  '
        filename = exporter.speech_filename(topic, "反方")
        self.assertEqual(filename, "教育-科技-发展-比较---------尾部-反方-一辩稿.docx")
        self.assertIsNone(re.search(r'[<>:"/\\|?*\x00-\x1f]', filename))
        self.assertFalse(filename.startswith(" "))
        self.assertNotIn("...-反方", filename)

    def test_filename_keeps_long_topic_while_directory_slug_is_limited(self):
        topic = "是否应该改变现有学习评价方式" * 8
        filename = exporter.speech_filename(topic, "正方")
        self.assertEqual(filename, f"{topic}-正方-一辩稿.docx")
        self.assertGreater(len(topic), 80)
        self.assertLessEqual(len(exporter.safe_slug(topic)), 80)

    def test_directory_slug_retains_ascii_letters_digits_and_decimal_points(self):
        self.assertEqual(exporter.safe_slug(" AI 2.0 2026 "), "AI-2.0-2026")
        self.assertEqual(exporter.safe_slug("AI/2.0:2026?"), "AI-2.0-2026")

    def test_windows_device_filename_is_made_writable(self):
        self.assertEqual(
            exporter.speech_filename("CON.txt", "正方"),
            "_CON.txt-正方-一辩稿.docx",
        )
        self.assertEqual(exporter.safe_slug("CON.txt"), "_CON.txt")

    def test_empty_filename_topic_has_readable_fallback(self):
        self.assertEqual(
            exporter.speech_filename(" .  ", "正方"),
            "未命名辩题-正方-一辩稿.docx",
        )


class DocxCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.products = self.root / "products"
        self.input_file = self.root / "draft.md"
        self.input_file.write_text(DRAFT, encoding="utf-8")

    def output_path(self, side="正方"):
        return self.products / f"{TOPIC}-{side}-一辩稿.docx"

    def assert_docx_retains_speech_and_sources(self, output_path):
        self.assertTrue(output_path.is_file())
        doc = Document(output_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("我方认为应该重视学习方式的变化", text)
        self.assertIn("这一判断需要结合具体条件理解。[1]", text)
        self.assertIn("参考文献", text)
        self.assertIn("https://example.org/research?year=2026", text)
        self.assertIn(TOPIC, doc.core_properties.title)
        self.assertNotEqual(output_path.name, "辩题-正方-一辩稿.docx")

    def run_export(self, *extra):
        args = [
            "export_to_docx.py", "--topic", TOPIC, "--side", "正方",
            "--input", str(self.input_file), "--products-dir", str(self.products),
            *extra,
        ]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", args), redirect_stdout(stdout), redirect_stderr(stderr):
            code = exporter.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def run_generator(self, *extra):
        args = [
            "generate_docx_with_model.py", "--topic", TOPIC, "--side", "反方",
            "--duration", "3分钟", "--products-dir", str(self.products),
            *extra,
        ]
        router = Mock()
        router.generate.return_value = SimpleNamespace(
            text=DRAFT, provider="offline_test", model="offline-model", response_id="test-response"
        )
        dotenv = SimpleNamespace(load_dotenv=Mock())
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", args),
            patch.dict(sys.modules, {"dotenv": dotenv}),
            patch.object(generator, "load_config", return_value=CONFIG),
            patch.object(generator, "ModelRouter", return_value=router) as router_class,
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = generator.main()
        return code, stdout.getvalue(), stderr.getvalue(), router_class, router

    def test_text_export_cli_creates_reopenable_docx_under_user_topic(self):
        code, stdout, stderr = self.run_export()
        self.assertEqual(code, 0, stderr)
        self.assert_docx_retains_speech_and_sources(self.output_path())
        self.assertIn(str(self.output_path().resolve()), stdout)

    def test_text_export_refuses_to_overwrite_existing_speech(self):
        self.assertEqual(self.run_export()[0], 0)
        output = self.output_path()
        before = output.read_bytes()
        with patch.object(exporter, "build_docx") as build:
            code, _, _ = self.run_export()
        self.assertEqual(code, 3)
        build.assert_not_called()
        self.assertEqual(output.read_bytes(), before)

    def test_mock_model_generation_creates_docx_and_preserves_references(self):
        code, stdout, stderr, router_class, router = self.run_generator()
        self.assertEqual(code, 0, stderr)
        router_class.assert_called_once_with(CONFIG)
        router.generate.assert_called_once()
        self.assert_docx_retains_speech_and_sources(self.output_path("反方"))
        self.assertIn(str(self.output_path("反方").resolve()), stdout)
        request = router.generate.call_args.kwargs
        self.assertIn(TOPIC, request["user_prompt"])
        self.assertIn("反方", request["user_prompt"])
        self.assertEqual(request["role"], "drafting")

    def test_model_cli_refuses_to_overwrite_before_calling_model(self):
        self.assertEqual(self.run_generator()[0], 0)
        output = self.output_path("反方")
        before = output.read_bytes()
        code, _, _, router_class, router = self.run_generator()
        self.assertEqual(code, 3)
        router_class.assert_not_called()
        router.generate.assert_not_called()
        self.assertEqual(output.read_bytes(), before)

    def test_model_dry_run_reports_actual_topic_filename_without_creating_file(self):
        code, stdout, stderr, router_class, router = self.run_generator("--dry-run")
        self.assertEqual(code, 0, stderr)
        self.assertIn(str(self.output_path("反方")), stdout)
        self.assertFalse(self.output_path("反方").exists())
        router_class.assert_not_called()
        router.generate.assert_not_called()


class PromptPolicyTests(unittest.TestCase):
    def test_prompts_require_own_case_and_prohibit_anticipated_rebuttals(self):
        system, user = generator.make_prompts(TOPIC, "正方", "3分钟", "已核验资料 [1]", "突出因果机制")
        self.assertRegex(system, r"(?:只写|仅写|专注)[^。\n]*本方立论")
        for prohibited_section in ("预设反驳", "反方预判"):
            with self.subTest(section=prohibited_section):
                self.assertRegex(
                    system,
                    rf"(?:不(?:包含|加入|设置|写)|禁止|不得)[^。\n]{{0,100}}{prohibited_section}",
                )
        self.assertNotRegex(system, r"(?:输出应包含|应包含|必须包含)[^。\n]*反方预判")
        self.assertIn(TOPIC, user)
        self.assertIn("已核验资料 [1]", user)
        self.assertIn("突出因果机制", user)


if __name__ == "__main__":
    unittest.main()
