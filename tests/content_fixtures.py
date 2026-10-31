"""Synthetic, explicitly offline fixtures; no public factual claims are verified."""
import json

PHENOMENON = '离线测试中的学习班采用即时反馈练习，学习者随后修改了先前的答案。[1]'
PHENOMENON_LINK = '这个测试情境让反馈怎样影响下一次作答变得可见，因而支持我方关注学习过程的判断。'
THEORY = '测试设定的反馈模型说明，行动者在收到可理解的结果信息后，可以据此调整下一次行动。[1]'
THEORY_LINK = '该模型在反馈可理解且行动允许调整的条件下解释修正过程，因而支持本方关于学习方式的论点。'
BODY = ('# AI与学习方式\n\n## 正文\n主席、评委、各位同学，大家好。'
        '我方认为应该重视学习方式的变化。\n'
        '当反馈更及时，学习者就能更快发现问题；这一判断需要结合具体条件理解。[1]\n'
        + PHENOMENON + '\n' + PHENOMENON_LINK + '\n' + THEORY + '\n' + THEORY_LINK)
SOURCES = {'sources': [{
    'id': '1', 'title': '示例资料（2026）',
    'locator': 'https://example.org/research?year=2026', 'kind': 'both',
    'verified': True, 'verification_note': '仅离线测试操作者声明，不是已核验公共事实',
    'summary': '用于测试来源绑定的虚构学习情境与反馈模型，不可用于实际稿件',
}]}


def model_payload():
    return {'body': BODY, 'requirements': {
        'phenomenon': {'excerpt': PHENOMENON, 'explanation': PHENOMENON_LINK, 'source_ids': ['1']},
        'theory': {'excerpt': THEORY, 'explanation': THEORY_LINK, 'source_ids': ['1']},
    }}


MODEL_RESPONSE = json.dumps(model_payload(), ensure_ascii=False)


def write_sources(path):
    path.write_text(json.dumps(SOURCES, ensure_ascii=False), encoding='utf-8')
    return path
