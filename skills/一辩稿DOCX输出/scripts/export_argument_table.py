#!/usr/bin/env python3
"""Export an explicitly requested argument collection as real Word tables.

The input must contain arguments with verified=true and public-source verification
notes. This script validates the JSON structure and declared status only: it does
not use the network, verify facts, or turn unknown/title-only sources into verified
evidence. verification_note describes checks of public evidence and any secondary
citation; it must not contain private reasoning or internal deliberation.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

from docx import Document
from export_to_docx import default_products_dir, speech_filename
from material_table_layout import HEADERS, COLUMN_WIDTHS_CM, append_material_table


CATEGORIES = ("进攻", "防守", "证明")
NO_MATERIAL_MESSAGE = "本次未找到可核验的相关论据"
TEXT_FIELDS = ("claim", "material", "usage", "limitation", "verification_note")
SOURCE_FIELDS = ("author", "title", "date", "url")
UNKNOWN_SOURCE_VALUES = frozenset({
    "未知", "未知来源", "来源未知", "不详", "暂无", "待核验", "未核验", "未查",
    "无出处", "无来源", "未提供", "待补充", "仅有标题", "unknown", "n/a", "none", "null",
})


def _text(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} 必须是非空字符串。")
    text = value.strip()
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]", text):
        raise ValueError(f"{field} 含有 Word 不支持的控制字符。")
    return text


def _source_url(value, field: str) -> str:
    url = _text(value, field)
    try:
        parts = urlsplit(url)
        valid = parts.scheme.lower() in {"http", "https"} and bool(parts.netloc) and bool(parts.hostname)
        # Accessing port also rejects malformed bracket/port syntax.
        parts.port
    except ValueError:
        valid = False
    if not valid or re.search(r"\s", url):
        raise ValueError(f"{field} 必须是完整的 http/https 来源链接。")
    return url


def validate_payload(payload) -> list[dict]:
    """Validate declarations without treating that validation as fact-checking."""
    if not isinstance(payload, dict) or not isinstance(payload.get("arguments"), list):
        raise ValueError("JSON 顶层必须是包含 arguments 数组的对象。")
    if not payload["arguments"]:
        raise ValueError("arguments 为空；本次没有可导出的已核验相关论据。")
    normalized = []
    seen_ids = set()
    for index, item in enumerate(payload["arguments"], 1):
        prefix = f"arguments[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} 必须是对象。")
        identifier = item.get("id")
        if isinstance(identifier, int) and not isinstance(identifier, bool):
            identifier = str(identifier)
        identifier = _text(identifier, f"{prefix}.id")
        if identifier in seen_ids:
            raise ValueError(f"论据 id 重复：{identifier}")
        seen_ids.add(identifier)
        if item.get("verified") is not True:
            raise ValueError(f"{prefix}.verified 必须为布尔 true；待核验条目不能导出。")
        categories = item.get("categories")
        if (not isinstance(categories, list) or not categories
                or any(not isinstance(category, str) or category not in CATEGORIES for category in categories)
                or len(set(categories)) != len(categories)):
            raise ValueError(f"{prefix}.categories 必须包含进攻、防守、证明中的一个或多个不同类别。")
        result = {"id": identifier, "verified": True, "categories": list(categories)}
        if 'group' in item:
            result['group'] = _text(item['group'], f'{prefix}.group')
        if 'encounter' in item:
            result['encounter'] = _text(item['encounter'], f'{prefix}.encounter')
        for field in TEXT_FIELDS:
            result[field] = _text(item.get(field), f"{prefix}.{field}")
        sources = item.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"{prefix}.sources 必须是非空来源数组，不能只有标题或未知出处。")
        result["sources"] = []
        for source_index, source in enumerate(sources, 1):
            source_prefix = f"{prefix}.sources[{source_index}]"
            if not isinstance(source, dict):
                raise ValueError(f"{source_prefix} 必须是对象。")
            checked = {}
            for field in SOURCE_FIELDS:
                text = _text(source.get(field), f"{source_prefix}.{field}")
                if text.lower() in UNKNOWN_SOURCE_VALUES:
                    raise ValueError(f"{source_prefix}.{field} 不能使用未知或待核验占位内容。")
                checked[field] = text
            checked["url"] = _source_url(checked["url"], f"{source_prefix}.url")
            if 'link_label' in source:
                checked['link_label'] = _text(source['link_label'], f'{source_prefix}.link_label')
            result["sources"].append(checked)
        normalized.append(result)
    return normalized


def argument_table_filename(topic: str, side: str) -> str:
    """Keep the full-topic filename sanitation used by speech exports."""
    filename = speech_filename(topic, side)
    return filename[:-len("一辩稿.docx")] + "论据资料表.docx"


def build_argument_document(arguments: list[dict], topic: str, side: str):
    """Build the shared reference-based portrait table after validation."""
    doc = Document()
    doc.core_properties.title = f"{topic} {side} 论据资料表"
    doc.core_properties.subject = "华语辩论论据资料表"
    doc.core_properties.keywords = "辩论,资料,来源,核验"
    append_material_table(doc, arguments, topic=topic, side=side, title='论据资料表')
    return doc


def check_saved_table(output_path: Path):
    doc = Document(output_path)
    if not any(len(table.columns) == 3
               and [cell.text for cell in table.rows[0].cells] == list(HEADERS)
               and any(len(row._tr.tc_lst) == 3 and row.cells[0].text.strip() for row in table.rows[1:])
               for table in doc.tables):
        raise RuntimeError("生成的 DOCX 未包含非空论据表格。")


def save_argument_document(doc, output_path: Path, *, force: bool):
    """Validate a saved temporary document and refuse accidental replacement."""
    buffer = BytesIO()
    doc.save(buffer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(suffix=".docx", prefix=".argument-table-", dir=output_path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(buffer.getvalue())
        check_saved_table(temporary_path)
        if force:
            os.replace(temporary_path, output_path)
        else:
            # Exclusive creation also protects a file created after the CLI check.
            created = False
            try:
                with output_path.open("xb") as output_file:
                    created = True
                    output_file.write(buffer.getvalue())
                check_saved_table(output_path)
            except Exception:
                if created:
                    output_path.unlink(missing_ok=True)
                raise
        check_saved_table(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def table_completion_message(products_dir: Path, *, default_location: bool) -> str:
    location = "桌面上的products" if default_location else str(products_dir.resolve())
    return f"论据资料表已保存，请在{location}文件夹中检查。"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将用户选择生成的已核验论据 JSON 导出为 Word 资料表。",
        epilog=("本脚本仅校验字段结构与 verified=true 声明，不联网、不自动核实事实。"
                "不得将仅有标题、未知出处或待核验条目标为已核验。verification_note 只记公开证据"
                "的核对结果和转引情况，不记录内部思考链。"),
    )
    parser.add_argument("--topic", required=True, help="用户询问的完整辩题")
    parser.add_argument("--side", required=True, choices=["正方", "反方"], help="立场")
    parser.add_argument("--input", required=True, help="UTF-8 JSON 文件，顶层含 arguments 数组")
    parser.add_argument("--products-dir", help="成品目录，默认系统桌面的 products；不建立辩题子目录")
    parser.add_argument("--force", action="store_true", help="明确允许覆盖同名资料表")
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        arguments = validate_payload(payload)
        products_dir = Path(args.products_dir).expanduser() if args.products_dir else default_products_dir()
        output_path = products_dir / argument_table_filename(args.topic, args.side)
        if output_path.exists() and not args.force:
            print(f"目标资料表已存在，为避免覆盖已停止：{output_path}。确认覆盖请增加 --force。", file=sys.stderr)
            return 3
        document = build_argument_document(arguments, args.topic, args.side)
        save_argument_document(document, output_path, force=args.force)
        print(output_path.resolve())
        print(table_completion_message(products_dir, default_location=args.products_dir is None))
        return 0
    except FileExistsError:
        print("目标资料表已存在，未覆盖；确认覆盖请增加 --force。", file=sys.stderr)
        return 3
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"资料表导出失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
