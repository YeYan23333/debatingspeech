"""One synthetic topic/framework/source set for recorded and unrecorded closings."""
import json

from tests.content_fixtures import (PHENOMENON, PHENOMENON_LINK, THEORY,
                                    THEORY_LINK, model_payload)

TOPIC = '课堂采用即时反馈是否更有利于学习'
SIDE = '正方'
DURATION = '3分钟'
FRAMEWORK = ('判准：在反馈可理解且允许修正的条件下，比较是否促进学习者修正问题。\n'
             '论点一：反馈帮助定位偏差。论点二：允许再作答才能把反馈转成调整。\n'
             '边界：不声称所有反馈对所有学生都有效，不改变同一比较标准。')
RECORD = ('本场模拟笔记，仅用于离线测试：\n'
          '对方提出：反馈可能帮助修正答案，但即时告知本身不保证理解。\n'
          '我方回应：框架已经限定反馈可理解且允许再次行动；比较应落在这些条件内。\n'
          '备注：这是笔记概述，不是逐字原话；未记录对方撤回原主张。')


def closing_response(*, recorded: bool) -> str:
    """Mock response content; it does not demonstrate a model's writing quality."""
    payload = model_payload()
    heading = '# 四辩总结\n' if recorded else '# 四辩总结 赛前预备稿\n'
    comparison = ('记录中的分歧在于反馈是否足以带来理解。我方仍需说明条件怎样使修正成为可能，'
                  '不能从对方提出条件就推断其撤回主张。' if recorded else
                  '如果对方采取“反馈不保证理解”的路线，我方需要比较反馈可理解且允许修正时的作用。'
                  '\n[现场交锋情况待补]\n')
    payload['body'] = (heading + '本题先比较反馈在既定条件下能否帮助修正问题。\n'
                       + comparison + '\n' + PHENOMENON + '\n' + PHENOMENON_LINK + '\n'
                       + THEORY + '\n' + THEORY_LINK + '\n'
                       '因此，在反馈可理解且允许再次行动的范围内，所述修正机制支持本方判断。')
    return json.dumps(payload, ensure_ascii=False)
