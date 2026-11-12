"""Shared portrait material-table layout distilled from the retained reference.

Inputs are normalized records from the two validated exporters. Formatting never
upgrades source verification, guesses material groups, or duplicates a record for
each use category. Source URLs remain complete external hyperlink targets.
"""
from __future__ import annotations

from collections import OrderedDict
import math
from urllib.parse import urlsplit

from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor
from docx.text.run import Run

from export_to_docx import set_run_font

HEADERS = ('可用资料摘要', '资料来源', '可核验链接')
COLUMN_WIDTHS_CM = (7.75, 5.10, 4.35)
DEFAULT_GROUP = '相关资料'
TABLE_HEADING = '一、总表'
USE_HEADING = '二、怎么用'
RISK_HEADING = '三、风险提示'


def _font(run, size: float, *, bold=False, face='宋体', color='000000'):
    set_run_font(run, east_asia=face, latin='Times New Roman')
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def _paragraph(paragraph, text: str, *, size=10.5, bold=False, face='宋体',
               before=0, after=4, line=1.08, keep_next=False, center=False):
    props = paragraph.paragraph_format
    props.space_before, props.space_after = Pt(before), Pt(after)
    props.line_spacing = line
    props.first_line_indent = Pt(0)
    props.keep_with_next = keep_next
    props.keep_together = False
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    _font(paragraph.add_run(text), size, bold=bold, face=face)
    return paragraph


def _cell_text(cell, text: str, *, first=False, size=8.5, bold=False, face='宋体', keep_next=False):
    paragraph = cell.paragraphs[0] if first else cell.add_paragraph()
    _paragraph(paragraph, text, size=size, bold=bold, face=face,
               before=1, after=1, line=1.15, keep_next=keep_next)
    wrap = OxmlElement('w:wordWrap')
    wrap.set(qn('w:val'), '0')
    paragraph._p.get_or_add_pPr().insert_element_before(
        wrap, 'w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN',
        'w:bidi', 'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind',
        'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
        'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl',
        'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange',
    )
    return paragraph


def _shade(cell, fill: str):
    shade = OxmlElement('w:shd')
    shade.set(qn('w:val'), 'clear')
    shade.set(qn('w:color'), 'auto')
    shade.set(qn('w:fill'), fill)
    props = cell._tc.get_or_add_tcPr()
    for old in list(props.findall(qn('w:shd'))):
        props.remove(old)
    props.insert_element_before(shade, 'w:noWrap', 'w:tcMar', 'w:textDirection',
                                'w:tcFitText', 'w:vAlign', 'w:hideMark', 'w:headers',
                                'w:cellIns', 'w:cellDel', 'w:cellMerge', 'w:tcPrChange')


def _cell_properties(cell, width):
    cell.width = width
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    margin = OxmlElement('w:tcMar')
    for name, twips in (('top', 30), ('left', 108), ('bottom', 30), ('right', 108)):
        node = OxmlElement('w:' + name)
        node.set(qn('w:w'), str(twips))
        node.set(qn('w:type'), 'dxa')
        margin.append(node)
    props = cell._tc.get_or_add_tcPr()
    for old in list(props.findall(qn('w:tcMar'))):
        props.remove(old)
    props.insert_element_before(margin, 'w:textDirection', 'w:tcFitText', 'w:vAlign',
                                'w:hideMark', 'w:headers', 'w:cellIns', 'w:cellDel',
                                'w:cellMerge', 'w:tcPrChange')
    # Word can suppress a table-level insideH edge after merged group rows.
    # Give every cell explicit edges so adjacent records keep a visible rule.
    props = cell._tc.get_or_add_tcPr()
    for old in list(props.findall(qn('w:tcBorders'))):
        props.remove(old)
    borders = OxmlElement('w:tcBorders')
    for name in ('top', 'left', 'bottom', 'right'):
        border = OxmlElement('w:' + name)
        for key, value in (('val', 'single'), ('sz', '4'), ('color', '999999')):
            border.set(qn('w:' + key), value)
        borders.append(border)
    props.insert_element_before(borders, 'w:shd', 'w:noWrap', 'w:tcMar', 'w:textDirection',
                                'w:tcFitText', 'w:vAlign', 'w:hideMark', 'w:headers',
                                'w:cellIns', 'w:cellDel', 'w:cellMerge', 'w:tcPrChange')


def _clear_title_borders(paragraph):
    """Override inherited Title rules locally, without changing earlier titles."""
    props = paragraph._p.get_or_add_pPr()
    for old in list(props.findall(qn('w:pBdr'))):
        props.remove(old)
    borders = OxmlElement('w:pBdr')
    for name in ('top', 'left', 'bottom', 'right', 'between', 'bar'):
        edge = OxmlElement('w:' + name)
        edge.set(qn('w:val'), 'nil')
        borders.append(edge)
    props.insert_element_before(
        borders, 'w:shd', 'w:tabs', 'w:suppressAutoHyphens', 'w:kinsoku', 'w:wordWrap',
        'w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN', 'w:bidi',
        'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind', 'w:contextualSpacing',
        'w:mirrorIndents', 'w:suppressOverlap', 'w:jc', 'w:textDirection', 'w:textAlignment',
        'w:textboxTightWrap', 'w:outlineLvl', 'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange',
    )


def _row_breaks(row, *, allow_split=False):
    props = row._tr.get_or_add_trPr()
    for old in list(props.findall(qn('w:cantSplit'))):
        props.remove(old)
    if not allow_split:
        props.insert_element_before(OxmlElement('w:cantSplit'), 'w:trHeight', 'w:tblHeader',
                                    'w:tblCellSpacing', 'w:jc', 'w:hidden', 'w:ins',
                                    'w:del', 'w:trPrChange')


def _link(cell, source: dict, number: int, *, first=False):
    paragraph = _cell_text(cell, '', first=first, size=7.5)
    url = source['url']
    label = source.get('link_label') or f'{urlsplit(url).netloc} 原文'
    node = OxmlElement('w:hyperlink')
    node.set(qn('r:id'), paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True))
    node.set(qn('w:history'), '1')
    run_node = OxmlElement('w:r')
    text = OxmlElement('w:t')
    text.text = f'[{number}] {label}'
    run_node.append(text)
    node.append(run_node)
    paragraph._p.append(node)
    run = Run(run_node, paragraph)
    _font(run, 7.5, color='1F4E79')
    run.font.underline = True


def configure_material_section(section):
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(2), Cm(2)
    section.left_margin, section.right_margin = Cm(1.9), Cm(1.9)
    section.header_distance = section.footer_distance = Cm(1.27)


def _table(doc):
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [Cm(value) for value in COLUMN_WIDTHS_CM]
    for column, width in zip(table.columns, widths):
        column.width = width
    props = table._tbl.tblPr
    total = sum(width.twips for width in widths)
    table_width = props.find(qn('w:tblW'))
    table_width.set(qn('w:type'), 'dxa')
    table_width.set(qn('w:w'), str(total))
    borders = OxmlElement('w:tblBorders')
    for name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        border = OxmlElement('w:' + name)
        for key, value in (('val', 'single'), ('sz', '4'), ('color', '999999')):
            border.set(qn('w:' + key), value)
        borders.append(border)
    props.insert_element_before(borders, 'w:shd', 'w:tblLayout', 'w:tblCellMar',
                                'w:tblLook', 'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    for cell, heading, width in zip(table.rows[0].cells, HEADERS, widths):
        _cell_properties(cell, width)
        _shade(cell, 'EDEDED')
        _cell_text(cell, heading, first=True, size=9, bold=True, face='黑体', keep_next=True)
    repeat = OxmlElement('w:tblHeader')
    repeat.set(qn('w:val'), 'true')
    table.rows[0]._tr.get_or_add_trPr().append(repeat)
    _row_breaks(table.rows[0])
    return table


def _heading(doc, text):
    return _paragraph(doc.add_paragraph(text='', style='Heading 1'), text,
                      size=14, bold=True, face='黑体', before=12, after=6, keep_next=True)


def _estimated_lines(text: str, characters: int) -> int:
    return sum(max(1, math.ceil(len(line) / characters)) for line in text.splitlines())


def append_material_table(doc, records: list[dict], *, topic='', side='',
                          title='资料表', new_section=False):
    """Append one three-column table and notes; callers supply validated records.

    Record fields: id, claim, material, sources; optional group, categories, usage,
    encounter, limitation, verification_note. Source fields include author, title,
    date, url and optional link_label. A group is never inferred from prose.
    """
    section = doc.add_section(WD_SECTION.NEW_PAGE) if new_section else doc.sections[-1]
    configure_material_section(section)
    # Direct paragraph/run formatting keeps an attached table from changing the
    # styles and font sizes used by an already-written speech or attack draft.
    title_paragraph = _paragraph(doc.add_paragraph(style='Title'), topic or title,
                                 size=16, bold=True, face='黑体', after=6, keep_next=True, center=True)
    _clear_title_borders(title_paragraph)
    _paragraph(doc.add_paragraph(), f'{side}资料表　可用资料摘要－资料来源－可核验链接',
               size=11, bold=True, face='黑体', after=6, keep_next=True, center=True)
    if topic or side:
        _paragraph(doc.add_paragraph(), f'辩题：{topic}　｜　立场：{side}',
                   size=9, after=4, keep_next=True)
    groups = OrderedDict()
    seen = set()
    for record in records:
        if record['id'] in seen:
            raise ValueError(f'资料编号重复，不能重复排入总表：{record["id"]}')
        seen.add(record['id'])
        groups.setdefault(record.get('group') or DEFAULT_GROUP, []).append(record)
    _paragraph(doc.add_paragraph(), f'资料数量：{len(records)} 条，共 {len(groups)} 组；每条资料仅列一次。',
               size=9, after=4, keep_next=True)
    _paragraph(doc.add_paragraph(),
               '核验分级：原文、摘要或转引的核对范围以各条核验说明为准；未注明时不推定已逐字核验。',
               size=9, after=4)
    _heading(doc, TABLE_HEADING)
    if not records:
        _paragraph(doc.add_paragraph(), '待补资料：未提供已核验来源短引，当前没有可排入总表的资料。', size=9)
        table = None
    else:
        table = _table(doc)
        widths = [Cm(value) for value in COLUMN_WIDTHS_CM]
        sequence = 0
        for group, selected in groups.items():
            row = table.add_row()
            merged = row.cells[0].merge(row.cells[-1])
            _cell_properties(merged, Cm(sum(COLUMN_WIDTHS_CM)))
            _shade(merged, 'F5F0E6')
            _cell_text(merged, group, first=True, size=9, bold=True, face='黑体', keep_next=True)
            _row_breaks(row)
            for record in selected:
                sequence += 1
                row = table.add_row()
                for cell, width in zip(row.cells, widths):
                    _cell_properties(cell, width)
                    _shade(cell, 'FFFFFF')
                _cell_text(row.cells[0], f'{sequence:02d}．[{record["id"]}]　{record["claim"]}', first=True, bold=True)
                _cell_text(row.cells[0], record['material'])
                categories = record.get('categories') or []
                if categories:
                    _cell_text(row.cells[0], '用途类别：' + '、'.join(categories), size=8)
                source_texts = []
                for index, source in enumerate(record['sources'], 1):
                    source_text = f'[{index}] {source["author"]}　{source["title"]}（{source["date"]}）'
                    source_texts.append(source_text)
                    _cell_text(row.cells[1], source_text, first=index == 1, size=8)
                    _link(row.cells[2], source, index, first=index == 1)
                note = record.get('verification_note') or '操作者已确认来源及短引；程序未联网核实。'
                _cell_text(row.cells[2], '核验说明：' + note, size=7.5, face='楷体')
                maximum_lines = max(
                    _estimated_lines(record['claim'] + '\n' + record['material'], 25) + 3,
                    _estimated_lines('\n'.join(source_texts), 17),
                    _estimated_lines(note, 16) + 2 * len(record['sources']),
                )
                _row_breaks(row, allow_split=maximum_lines > 48)
    _heading(doc, USE_HEADING)
    if not records:
        _paragraph(doc.add_paragraph(), '补充已核验资料后，再按本场判准安排其证明位置。')
    for record in records:
        use = record.get('usage') or '结合已确认框架使用，具体证明关系需由使用者补充。'
        encounter = record.get('encounter')
        if encounter:
            use += '　适用交锋：' + encounter
        _paragraph(doc.add_paragraph(), f'{record["id"]}：{use}')
    _heading(doc, RISK_HEADING)
    _paragraph(doc.add_paragraph(), '本表仅校验输入结构和操作者的核验声明，程序未联网核实事实；短引不能替代完整原文及其适用条件。')
    for record in records:
        if record.get('limitation'):
            _paragraph(doc.add_paragraph(), f'{record["id"]}：{record["limitation"]}')
    return table
