"""Check speech pacing and the single-entry Skill package without network access."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PROJECT_ROOT / "skills" / "一辩稿DOCX输出" / "scripts"
for import_dir in (PROJECT_ROOT, SCRIPT_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))


def load_generator():
    name = "_pacing_generate_docx_with_model"
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / "generate_docx_with_model.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load model generation script")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


generator = load_generator()


class WordBudgetTests(unittest.TestCase):
    def test_supported_duration_formats_produce_consistent_word_budgets(self):
        cases = {
            "1分钟": (310, 325, 340),
            "2分30秒": (775, 813, 850),
            "3分钟": (930, 975, 1020),
            "3分30秒": (1085, 1138, 1190),
            "2:30": (775, 813, 850),
            "150秒": (775, 813, 850),
            "2.5分钟": (775, 813, 850),
        }
        for duration, expected in cases.items():
            with self.subTest(duration=duration):
                self.assertEqual(generator.word_budget(duration), expected)

    def test_unparsed_duration_keeps_the_missing_budget_explicit(self):
        self.assertIsNone(generator.word_budget("按赛制"))

    def test_prompts_receive_actual_duration_budget(self):
        for duration, expected in (
            ("1分钟", (310, 325, 340)),
            ("3分钟", (930, 975, 1020)),
            ("3分30秒", (1085, 1138, 1190)),
        ):
            with self.subTest(duration=duration):
                system, user = generator.make_prompts(
                    "人工智能是否改变学习方式？", "正方", duration,
                    "未提供事实资料。", "突出关键因果机制。",
                )
                prompts = f"{system}\n{user}"
                numbers = set(re.findall(r"(?<!\d)\d+(?!\d)", prompts))
                for word_count in expected:
                    self.assertIn(str(word_count), numbers)
                self.assertIn(duration, user)
                self.assertNotRegex(prompts, r"(?<!\d)(?:250|280)(?!\d)")


class SingleSkillPackageTests(unittest.TestCase):
    def test_root_is_the_only_skill_entry_point(self):
        entries = sorted(
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in PROJECT_ROOT.rglob("SKILL.md")
            if "__pycache__" not in path.parts
        )
        self.assertEqual(entries, ["SKILL.md"])
        skill = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
        front_matter = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", skill, re.S)
        self.assertIsNotNone(front_matter, "Root Skill must retain YAML front matter")
        self.assertRegex(front_matter.group(1), r"(?m)^name:\s*debatingspeech\s*$")

    def test_root_skill_and_loaded_style_guide_use_current_pacing(self):
        for relative in ("SKILL.md", "references/natural-first-speaker-style.md"):
            with self.subTest(file=relative):
                text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
                self.assertNotRegex(text, r"(?<!\d)(?:250|280)(?!\d)")
                numbers = set(re.findall(r"(?<!\d)\d+(?!\d)", text))
                self.assertTrue({"310", "325", "340"}.issubset(numbers))

    def test_consolidated_reference_and_docx_scripts_remain_available(self):
        for relative in (
            "references/api调用教程.md",
            "references/docx-output.md",
            "skills/一辩稿DOCX输出/scripts/export_to_docx.py",
            "skills/一辩稿DOCX输出/scripts/generate_docx_with_model.py",
        ):
            with self.subTest(path=relative):
                target = PROJECT_ROOT / relative
                self.assertTrue(target.is_file(), f"Required resource is missing: {relative}")
                self.assertTrue(target.read_text(encoding="utf-8").strip())

    def test_root_documentation_local_markdown_links_resolve(self):
        for relative in ("SKILL.md", "README.md"):
            document = PROJECT_ROOT / relative
            text = document.read_text(encoding="utf-8")
            # Root docs use ordinary inline Markdown links; web links and section
            # anchors are intentionally outside this filesystem check.
            targets = re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text)
            for raw_target in targets:
                target = raw_target.strip().strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                local = document.parent / unquote(parsed.path)
                with self.subTest(document=relative, link=target):
                    self.assertTrue(local.exists(), f"Broken local link in {relative}: {target}")


if __name__ == "__main__":
    unittest.main()
