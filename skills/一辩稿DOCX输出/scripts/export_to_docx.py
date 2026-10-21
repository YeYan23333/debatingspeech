#!/usr/bin/env python3
"""Convert a debate speech draft to a formatted DOCX in the desktop products folder.

Input can be a text/Markdown file or stdin. The script does not require API access.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.section import WD_SECTION
    from docx.shared import Cm, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
except ImportError as exc:
    raise SystemExit(
        "缺少 python-docx 依赖。请执行：pip install python-docx"
    ) from exc


SUCCESS_MESSAGE = "请在桌面上的products文件夹中检查，如不满意请继续提出您的修改意见，我将继续为您修改"


def _windows_desktop_directory() -> Path:
    """Resolve the current user's real desktop, including redirected locations."""
    import ctypes
    from ctypes import wintypes
    import uuid

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    desktop_id = GUID.from_buffer_copy(uuid.UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641").bytes_le)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    ole32 = ctypes.WinDLL("ole32", use_last_error=True)
    get_path = shell32.SHGetKnownFolderPath
    get_path.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)]
    get_path.restype = ctypes.c_long
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None
    pointer = ctypes.c_wchar_p()
    try:
        result = get_path(ctypes.byref(desktop_id), 0, None, ctypes.byref(pointer))
        if result != 0 or not pointer.value:
            raise OSError(f"无法读取系统桌面位置（HRESULT={result}）")
        return Path(pointer.value)
    finally:
        if pointer:
            ole32.CoTaskMemFree(ctypes.cast(pointer, ctypes.c_void_p))


def desktop_directory() -> Path:
    """Locate the desktop without creating any folder."""
    if os.name == "nt":
        try:
            return _windows_desktop_directory()
        except (OSError, AttributeError, ValueError):
            try:
                import winreg
                key_name = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name) as key:
                    value, _ = winreg.QueryValueEx(key, "Desktop")
                resolved = Path(os.path.expandvars(value))
                if resolved.is_absolute():
                    return resolved
            except (OSError, TypeError, ValueError):
                pass
            raise RuntimeError("无法确定系统桌面位置；请用 --products-dir 指定成品目录。")
    return Path.home() / "Desktop"


def default_products_dir() -> Path:
    """Return the desktop products path; creation happens only on successful save."""
    return desktop_directory() / "products"


def completion_message(products_dir: Path, *, default_location: bool) -> str:
    if default_location:
        return SUCCESS_MESSAGE
    return f"请在{products_dir.resolve()}文件夹中检查，如不满意请继续提出您的修改意见，我将继续为您修改"


def safe_slug(topic: str) -> str:
    """Create a stable, readable directory name from the debate topic."""
    value = unicodedata.normalize("NFKC", topic).strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip(" .-_")
    value = value[:80].rstrip(" .") or "未命名辩题"
    if re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", value):
        value = "_" + value
    return value


def speech_filename(topic: str, side: str) -> str:
    """Use the user's full topic in the filename, preserving legal punctuation."""
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", topic).strip().rstrip(" .")
    filename = f"{value or '未命名辩题'}-{side}-一辩稿.docx"
    if re.match(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])\.", filename):
        filename = "_" + filename
    return filename


def set_run_font(run, east_asia: str = "宋体", latin: str = "Times New Roman"):
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), east_asia)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)


def set_style_font(style, east_asia: str = "宋体", latin: str = "Times New Roman"):
    style.font.name = latin
    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), east_asia)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)


def add_formatted_runs(paragraph, text: str):
    """Render simple **bold**, *italic*, and inline-code syntax as Word runs."""
    # Keep the parser intentionally simple and predictable for speech drafts.
    pattern = re.compile(r"(\*\*.*?\*\*|(?<!\*)\*[^*]+\*(?!\*)|`[^`]+`)")
    cursor = 0
    for match in pattern.finditer(text):
        if match.start() > cursor:
            run = paragraph.add_run(text[cursor:match.start()])
            set_run_font(run)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
        else:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        set_run_font(run)
        cursor = match.end()
    if cursor < len(text):
        run = paragraph.add_run(text[cursor:])
        set_run_font(run)


def is_metadata_line(line: str) -> bool:
    return bool(re.match(r"^\s*[-*]\s*\*\*?(辩题|立场|目标时长|正文约字数|预计口播时间)\*\*?\s*[:：]", line))


def parse_line(doc: Document, line: str, *, first_title_used: bool, topic: str, side: str):
    stripped = line.strip()
    if not stripped:
        return first_title_used

    # Horizontal separators are omitted.
    if re.fullmatch(r"[-*_]{3,}", stripped):
        return first_title_used

    # Headings
    heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
    if heading:
        level = len(heading.group(1))
        title = heading.group(2).strip()
        if not first_title_used and level == 1:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(12)
            run = p.add_run(title)
            run.bold = True
            run.font.size = Pt(18)
            set_run_font(run, east_asia="黑体")
            return True
        p = doc.add_paragraph(style=f"Heading {min(level, 3)}")
        add_formatted_runs(p, title)
        return first_title_used

    # Block quote
    if stripped.startswith(">"):
        p = doc.add_paragraph(style="Quote")
        add_formatted_runs(p, stripped.lstrip("> ").strip())
        return first_title_used

    # Bullets and numbered lists
    bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
    if bullet:
        p = doc.add_paragraph(style="List Bullet")
        add_formatted_runs(p, bullet.group(1))
        return first_title_used

    numbered = re.match(r"^\d+[.)、]\s+(.+)$", stripped)
    if numbered:
        p = doc.add_paragraph(style="List Number")
        add_formatted_runs(p, numbered.group(1))
        return first_title_used

    # Metadata is made compact but remains visible.
    if is_metadata_line(stripped):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        add_formatted_runs(p, re.sub(r"^\s*[-*]\s*", "", stripped))
        for run in p.runs:
            run.font.size = Pt(10)
        return first_title_used

    # Main prose and reference list lines
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(5)
    if stripped.startswith("[") and re.match(r"^\[\d+\]", stripped):
        p.paragraph_format.left_indent = Cm(0.4)
        p.paragraph_format.first_line_indent = Cm(-0.4)
        p.paragraph_format.space_after = Pt(3)
        for run in p.runs:
            run.font.size = Pt(9)
    add_formatted_runs(p, stripped)
    if stripped.startswith("[") and re.match(r"^\[\d+\]", stripped):
        for run in p.runs:
            run.font.size = Pt(9)
    return first_title_used


def build_docx(text: str, topic: str, side: str, output_path: Path):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    set_style_font(doc.styles["Normal"], "宋体")
    doc.styles["Normal"].font.size = Pt(11)
    doc.styles["Normal"].paragraph_format.space_after = Pt(5)
    for style_name in ["Heading 1", "Heading 2", "Heading 3"]:
        set_style_font(doc.styles[style_name], "黑体")
    set_style_font(doc.styles["Quote"], "楷体")

    # Add consistent document properties.
    doc.core_properties.title = f"{topic} - {side} - 一辩稿"
    doc.core_properties.subject = "华语辩论一辩稿"
    doc.core_properties.keywords = "辩论,一辩稿"

    first_title_used = False
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for line in lines:
        first_title_used = parse_line(
            doc, line, first_title_used=first_title_used, topic=topic, side=side
        )

    # If the input contains no heading at all, add a title and metadata to the top.
    if not any(p.style.name.startswith("Heading") for p in doc.paragraphs) and not first_title_used:
        title_p = doc.paragraphs[0] if doc.paragraphs else doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_p.add_run(f"{topic}｜{side}一辩稿")
        title_run.bold = True
        title_run.font.size = Pt(18)
        set_run_font(title_run, east_asia="黑体")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="将一辩稿转换为 Word DOCX 并保存到 products 目录")
    parser.add_argument("--topic", required=True, help="用户询问的完整辩题，用于文档标题和文件名")
    parser.add_argument("--side", required=True, choices=["正方", "反方"], help="辩论立场")
    parser.add_argument("--input", default="-", help="输入文本文件路径；默认从标准输入读取")
    parser.add_argument("--products-dir", default=None, help="成品目录，默认系统桌面上的 products 文件夹")
    parser.add_argument("--force", action="store_true", help="允许覆盖目标文件；默认不覆盖")
    args = parser.parse_args()

    if args.input == "-":
        source_text = sys.stdin.read()
    else:
        input_path = Path(args.input)
        if not input_path.is_file():
            print(f"找不到输入稿件：{input_path}", file=sys.stderr)
            return 2
        source_text = input_path.read_text(encoding="utf-8")

    if not source_text.strip():
        print("输入稿件为空；请提供完整的一辩稿文本。", file=sys.stderr)
        return 2

    try:
        out_dir = Path(args.products_dir).expanduser() if args.products_dir else default_products_dir()
    except (OSError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    filename = speech_filename(args.topic, args.side)
    output_path = out_dir / filename
    if output_path.exists() and not args.force:
        print(
            f"目标文件已存在，为避免覆盖旧稿已停止：{output_path}\n"
            "如确认覆盖，请增加 --force；否则可先备份旧文件。",
            file=sys.stderr,
        )
        return 3

    try:
        build_docx(source_text, args.topic, args.side, output_path)
        # Validate the generated DOCX can be reopened and contains paragraphs.
        check = Document(output_path)
    except OSError as exc:
        print(f"保存DOCX失败：{exc}", file=sys.stderr)
        return 2
    paragraph_text = "\n".join(p.text for p in check.paragraphs).strip()
    if not paragraph_text:
        output_path.unlink(missing_ok=True)
        print("生成的 DOCX 未包含可读取正文，已删除异常文件。", file=sys.stderr)
        return 4

    print(output_path.resolve())
    print(completion_message(out_dir, default_location=args.products_dir is None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
