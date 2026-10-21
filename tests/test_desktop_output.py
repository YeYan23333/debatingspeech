"""Verify desktop products delivery using a temporary redirected desktop only."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from docx import Document

try:
    from . import test_docx_output as fixtures
except ImportError:
    import test_docx_output as fixtures


exporter = fixtures.exporter
generator = fixtures.generator
CLOSING = "请在桌面上的products文件夹中检查，如不满意请继续提出您的修改意见，我将继续为您修改"


class DesktopOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.desktop = self.root / "重定向后的桌面"
        self.products = self.desktop / "products"
        self.input_file = self.root / "draft.md"
        self.input_file.write_text(fixtures.DRAFT, encoding="utf-8")
        desktop_patch = patch.object(exporter, "desktop_directory", return_value=self.desktop)
        self.desktop_mock = desktop_patch.start()
        self.addCleanup(desktop_patch.stop)

    def output_path(self, side="正方", products=None):
        return (products or self.products) / f"{fixtures.TOPIC}-{side}-一辩稿.docx"

    def assert_readable_flat_docx(self, side="正方", products=None):
        folder = products or self.products
        output = self.output_path(side, folder)
        self.assertTrue(output.is_file())
        self.assertEqual(output.parent, folder)
        self.assertEqual(list(folder.glob("*.docx")), [output])
        self.assertFalse(any(path.is_dir() for path in folder.iterdir()))
        doc = Document(output)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        self.assertIn("我方认为应该重视学习方式的变化", text)
        self.assertIn("https://example.org/research?year=2026", text)
        return output

    def run_export(self, *extra):
        argv = [
            "export_to_docx.py", "--topic", fixtures.TOPIC, "--side", "正方",
            "--input", str(self.input_file), *extra,
        ]
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", argv), redirect_stdout(stdout), redirect_stderr(stderr):
            code = exporter.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def run_generator(self, *extra, model_failure=None):
        argv = [
            "generate_docx_with_model.py", "--topic", fixtures.TOPIC, "--side", "反方",
            "--duration", "3分钟", *extra,
        ]
        router = Mock()
        if model_failure is not None:
            router.generate.side_effect = model_failure
        else:
            router.generate.return_value = SimpleNamespace(
                text=fixtures.DRAFT, provider="offline_test", model="offline-model", response_id="test-response"
            )
        dotenv = SimpleNamespace(load_dotenv=Mock())
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.dict(sys.modules, {"dotenv": dotenv}),
            patch.object(generator, "load_config", return_value=fixtures.CONFIG),
            patch.object(generator, "ModelRouter", return_value=router) as router_class,
            redirect_stdout(stdout), redirect_stderr(stderr),
        ):
            code = generator.main()
        return code, stdout.getvalue(), stderr.getvalue(), router_class, router

    def test_default_products_uses_selected_desktop_without_creating_directory(self):
        self.assertEqual(exporter.default_products_dir(), self.products)
        self.desktop_mock.assert_called()
        self.assertFalse(self.products.exists())
        self.assertFalse(self.desktop.exists())

    def test_completion_message_distinguishes_default_and_custom_locations(self):
        self.assertEqual(exporter.completion_message(self.products, default_location=True), CLOSING)
        custom = self.root / "专用稿件目录"
        message = exporter.completion_message(custom, default_location=False)
        self.assertIn(str(custom.resolve()), message)
        self.assertNotIn("桌面上的products文件夹", message)

    def test_export_default_cli_delivers_flat_docx_and_requested_closing(self):
        code, stdout, stderr = self.run_export()
        self.assertEqual(code, 0, stderr)
        output = self.assert_readable_flat_docx()
        self.assertIn(str(output.resolve()), stdout)
        self.assertIn(CLOSING, stdout)

    def test_model_default_cli_delivers_flat_docx_and_requested_closing(self):
        code, stdout, stderr, router_class, router = self.run_generator()
        self.assertEqual(code, 0, stderr)
        output = self.assert_readable_flat_docx("反方")
        self.assertIn(str(output.resolve()), stdout)
        self.assertIn(CLOSING, stdout)
        router_class.assert_called_once_with(fixtures.CONFIG)
        router.generate.assert_called_once()

    def test_model_dry_run_reports_default_path_without_creating_directory_or_success(self):
        code, stdout, stderr, router_class, router = self.run_generator("--dry-run")
        self.assertEqual(code, 0, stderr)
        self.assertIn(str(self.output_path("反方")), stdout)
        self.assertFalse(self.products.exists())
        self.assertFalse(self.desktop.exists())
        self.assertNotIn(CLOSING, stdout + stderr)
        router_class.assert_not_called()
        router.generate.assert_not_called()

    def test_empty_export_input_does_not_create_output_or_claim_success(self):
        self.input_file.write_text("  \n", encoding="utf-8")
        code, stdout, stderr = self.run_export()
        self.assertNotEqual(code, 0)
        self.assertFalse(self.products.exists())
        self.assertNotIn(CLOSING, stdout + stderr)

    def test_model_failure_does_not_create_output_or_claim_success(self):
        code, stdout, stderr, _, router = self.run_generator(
            model_failure=generator.ProviderError("模拟离线错误")
        )
        self.assertNotEqual(code, 0)
        self.assertFalse(self.products.exists())
        self.assertNotIn(CLOSING, stdout + stderr)
        router.generate.assert_called_once()

    def test_existing_export_is_preserved_without_success_closing(self):
        self.assertEqual(self.run_export()[0], 0)
        output = self.output_path()
        before = output.read_bytes()
        code, stdout, stderr = self.run_export()
        self.assertEqual(code, 3)
        self.assertEqual(output.read_bytes(), before)
        self.assertNotIn(CLOSING, stdout + stderr)

    def test_custom_export_directory_is_flat_and_reported_truthfully(self):
        custom = self.root / "其他成品目录"
        code, stdout, stderr = self.run_export("--products-dir", str(custom))
        self.assertEqual(code, 0, stderr)
        self.assert_readable_flat_docx(products=custom)
        self.assertIn(str(custom.resolve()), stdout)
        self.assertNotIn("桌面上的products文件夹", stdout + stderr)
        self.assertFalse(self.products.exists())

    def test_custom_model_directory_is_flat_and_reported_truthfully(self):
        custom = self.root / "其他API成品目录"
        code, stdout, stderr, _, _ = self.run_generator("--products-dir", str(custom))
        self.assertEqual(code, 0, stderr)
        self.assert_readable_flat_docx("反方", products=custom)
        self.assertIn(str(custom.resolve()), stdout)
        self.assertNotIn("桌面上的products文件夹", stdout + stderr)
        self.assertFalse(self.products.exists())

    def test_package_does_not_contain_a_products_output_directory(self):
        self.assertFalse((fixtures.PROJECT_ROOT / "skills" / "products").exists())


if __name__ == "__main__":
    unittest.main()
