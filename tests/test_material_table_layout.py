"""Reference-layout invariants shared by standalone and attached material tables.

All records below are synthetic offline fixtures, never verified public evidence.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from tests.test_argument_table_output import ARGUMENT, exporter
from tests.test_debate_workflow import workflow
from material_table_layout import HEADERS, COLUMN_WIDTHS_CM


class MaterialTableLayoutTests(unittest.TestCase):
    def test_generated_property_sequences_follow_wordprocessingml_order(self):
        doc = exporter.build_argument_document(
            exporter.validate_payload({'arguments': [deepcopy(ARGUMENT)]}), '测试', '正方')
        # These are ordered schema children, not independent unordered settings.
        # Word can silently ignore a border appended after layout or alignment.
        orders = {
            'tblPr': ['tblW', 'jc', 'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook'],
            'tcPr': ['tcW', 'gridSpan', 'tcBorders', 'shd', 'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign'],
            'trPr': ['cantSplit', 'trHeight', 'tblHeader', 'tblCellSpacing', 'jc'],
            'pPr': ['pStyle', 'keepNext', 'keepLines', 'pBdr', 'shd', 'wordWrap', 'spacing', 'ind', 'jc'],
        }
        for name, sequence in orders.items():
            positions = {qn('w:' + item): index for index, item in enumerate(sequence)}
            nodes = doc._element.findall('.//' + qn('w:' + name))
            self.assertTrue(nodes)
            for node in nodes:
                present = [positions[child.tag] for child in node if child.tag in positions]
                self.assertEqual(present, sorted(present), f'{name} children out of schema order')

    def test_explicit_material_groups_are_stable_and_use_categories_do_not_duplicate_records(self):
        records = []
        for index, group in enumerate(('学理资料', '原文资料', '学理资料', None), 1):
            record = deepcopy(ARGUMENT)
            record.update(id=f'T{index}', claim=f'第{index}条唯一测试主张')
            if group:
                record['group'] = group
            records.append(record)
        doc = exporter.build_argument_document(exporter.validate_payload({'arguments': records}), '测试', '正方')
        table = doc.tables[0]
        self.assertEqual(len(doc.tables), 1)
        groups = [row.cells[0].text for row in table.rows[1:] if len(row._tr.tc_lst) == 1]
        self.assertEqual(groups, ['学理资料', '原文资料', '相关资料'])
        data = [row.cells[0].text for row in table.rows[1:] if len(row._tr.tc_lst) == 3]
        self.assertEqual(len(data), 4)
        self.assertTrue(data[0].startswith('01．[T1]'))
        self.assertTrue(data[1].startswith('02．[T3]'))
        self.assertTrue(data[2].startswith('03．[T2]'))
        self.assertTrue(data[3].startswith('04．[T4]'))
        for record in records:
            self.assertEqual(sum(record['claim'] in text for text in data), 1)
        for row in table.rows[1:]:
            if len(row._tr.tc_lst) == 1:
                self.assertTrue(row.cells[0].paragraphs[0].paragraph_format.keep_with_next)

    def test_multiple_sources_keep_label_target_pairing_and_verification_scope(self):
        record = deepcopy(ARGUMENT)
        record['sources'][0]['link_label'] = '第一来源 精确段落'
        record['sources'].append({
            'author': '第二测试作者', 'title': '第二测试记录', 'date': '2026-11-11',
            'url': 'https://example.net/path/' + 'long-' * 35 + '?a=1&b=2#exact',
            'link_label': '第二来源 表2',
        })
        doc = exporter.build_argument_document(exporter.validate_payload({'arguments': [record]}), '测试', '反方')
        row = doc.tables[0].rows[2]
        self.assertIn('[1] 测试资料机构', row.cells[1].text)
        self.assertIn('[2] 第二测试作者', row.cells[1].text)
        self.assertIn(record['verification_note'], row.cells[2].text)
        links = row.cells[2]._tc.findall('.//' + qn('w:hyperlink'))
        self.assertEqual(len(links), 2)
        for index, link in enumerate(links):
            self.assertEqual(doc.part.rels[link.get(qn('r:id'))].target_ref, record['sources'][index]['url'])
            self.assertIn(record['sources'][index]['link_label'], ''.join(link.itertext()))

    def test_only_oversized_records_may_split_and_rows_never_have_exact_heights(self):
        short = deepcopy(ARGUMENT)
        long = deepcopy(ARGUMENT)
        long.update(id='LONG', material='超长排版测试内容' * 300)
        doc = exporter.build_argument_document(exporter.validate_payload({'arguments': [short, long]}), '测试', '正方')
        short_row, long_row = doc.tables[0].rows[2:]
        self.assertIsNotNone(short_row._tr.trPr.find(qn('w:cantSplit')))
        self.assertIsNone(long_row._tr.trPr.find(qn('w:cantSplit')))
        for row in doc.tables[0].rows:
            self.assertIsNone(row._tr.trPr.find(qn('w:trHeight')))

    def test_attack_appendix_shares_layout_without_changing_previous_section_or_body_style(self):
        doc = Document()
        original = doc.sections[0]
        original.left_margin, original.right_margin = Cm(2.7), Cm(2.6)
        doc.styles['Normal'].font.size = Pt(14)
        original_title_style = doc.styles['Title']._element.xml
        doc.add_paragraph('这是既有攻防正文，不应被附表样式缩小。')
        evidence = [{
            'id': 'E1', 'claim': '离线测试命题', 'quote': '离线测试短引',
            'url': 'https://example.org/checked', 'title': '测试记录', 'author': '测试机构',
            'date': '2026-11-11', 'usage': '用于加固机制', 'encounter': '假设追问机制',
            'limitation': '仅说明排版', 'verified': True, 'quote_confirmed': True,
            'group': '原文资料', 'link_label': '测试来源定位', 'verification_note': '测试人工核对范围',
        }]
        workflow.append_evidence_table(doc, evidence, topic='测试辩题', side='反方')
        self.assertEqual(len(doc.sections), 2)
        self.assertAlmostEqual(doc.sections[0].left_margin / Cm(1), 2.7, places=2)
        self.assertAlmostEqual(doc.sections[0].right_margin / Cm(1), 2.6, places=2)
        self.assertEqual(doc.styles['Normal'].font.size, Pt(14))
        self.assertEqual(doc.styles['Title']._element.xml, original_title_style)
        table_title = next(p for p in doc.paragraphs if p.text == '测试辩题')
        title_edges = table_title._p.pPr.find(qn('w:pBdr'))
        self.assertIsNotNone(title_edges)
        self.assertTrue(all(edge.get(qn('w:val')) == 'nil' for edge in title_edges))
        self.assertAlmostEqual(doc.sections[-1].left_margin / Cm(1), 1.9, places=2)
        self.assertEqual([c.text for c in doc.tables[0].rows[0].cells], list(HEADERS))
        self.assertEqual(doc.tables[0].rows[1].cells[0].text, '原文资料')
        self.assertIn('离线测试短引', doc.tables[0].rows[2].cells[0].text)
        self.assertIn('测试人工核对范围', doc.tables[0].rows[2].cells[2].text)
        for column, width in zip(doc.tables[0].columns, COLUMN_WIDTHS_CM):
            self.assertAlmostEqual(column.width / Cm(1), width, places=2)
        for row in doc.tables[0].rows:
            for cell in row.cells:
                for edge in ('top', 'left', 'bottom', 'right'):
                    border = cell._tc.tcPr.find(qn('w:tcBorders')).find(qn('w:' + edge))
                    self.assertEqual(border.get(qn('w:val')), 'single')
                    self.assertEqual(border.get(qn('w:sz')), '4')
                    self.assertEqual(border.get(qn('w:color')), '999999')
        paragraphs = '\n'.join(p.text for p in doc.paragraphs)
        for field in ('usage', 'encounter', 'limitation'):
            self.assertIn(evidence[0][field], paragraphs)

    def test_optional_layout_metadata_is_validated_instead_of_dropping_controls_or_bad_types(self):
        for name, value in (('group', []), ('group', ' \n'), ('encounter', '\x00bad')):
            record = deepcopy(ARGUMENT)
            record[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                exporter.validate_payload({'arguments': [record]})
        record = deepcopy(ARGUMENT)
        record['sources'][0]['link_label'] = '\x00unsafe'
        with self.assertRaises(ValueError):
            exporter.validate_payload({'arguments': [record]})

    def test_evidence_layout_options_preserve_original_short_quote_gates(self):
        original = {
            'id': 'E1', 'claim': '测试主张', 'quote': '短引', 'url': 'https://example.org/original',
            'title': '测试来源', 'author': '测试作者', 'date': '2026-11-11', 'usage': '证明',
            'limitation': '仅离线', 'encounter': '测试交锋', 'verified': True, 'quote_confirmed': True,
            'group': '原文资料', 'link_label': '来源定位', 'verification_note': '核对范围',
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'evidence.json'
            path.write_text(json.dumps({'evidence': [original]}), encoding='utf8')
            checked = workflow.load_evidence(str(path))[0]
            for field in ('group', 'link_label', 'verification_note'):
                self.assertEqual(checked[field], original[field])
            for change in ({'quote_confirmed': False}, {'verified': False},
                           {'quote': '字' * 46}, {'quote': 'word ' * 26},
                           {'group': []}, {'link_label': '\x00bad'}):
                candidate = deepcopy(original) | change
                path.write_text(json.dumps({'evidence': [candidate]}), encoding='utf8')
                with self.subTest(change=change), self.assertRaises(ValueError):
                    workflow.load_evidence(str(path))


if __name__ == '__main__':
    unittest.main()
