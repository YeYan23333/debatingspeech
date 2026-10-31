# 上游来源记录

- 仓库：https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill/tree/main
- 分支：main
- Skill：https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill/blob/main/skills/anti-defensive-writing/SKILL.md
- Raw：https://raw.githubusercontent.com/Adkid-Zephyr/anti-defensive-writing-Skill/main/skills/anti-defensive-writing/SKILL.md
- 许可：https://raw.githubusercontent.com/Adkid-Zephyr/anti-defensive-writing-Skill/main/LICENSE
- 读取日期：2026-10-31（Asia/Shanghai）
- 获取方式：web 工具分别读取 raw 全文与 GitHub 文件页，以可见文本转录保存。未通过 shell 下载到上游原始字节，因此本文件不是经上游文件哈希确认的字节副本。原文规则完整保留，换行可能与原文件不同；description 中的〖防御性写作〗按 GitHub 文件页还原，消除 raw 网页工具将该括号误识别成引用标记的显示产物。
- 该中文 skill 文件夹在所读目录列表中仅含 SKILL.md；没有必需脚本、依赖或额外资源。
- 当前 main HEAD：未通过 API 确认，不填写。
- 辅助历史信息：所读提交历史页 https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill/commits/main/ 的首条是 b32067b3055d356e007c6986775fee069da3891a（2026-08-31），页面有缓存；该值不声称为本次 raw 内容对应的已验证 HEAD。
- 许可：MIT，保留同目录 LICENSE 的版权与许可全文。

## 接入辩论工作流建议

将本目录作为包内 `skills/anti-defensive-writing/`，主 skill 和模型提示词显式路由到该文件及已有 `references/debate-anti-defensive-writing.md`。后者是辩论适配规范，前者保留上游学术语境，不把其中“更换评价维度”“重新定义故事”直接等同于允许偷换辩题、框架或胜负标准。若需要系统级独立发现，须由根任务在授权目录安装；嵌套包内 SKILL.md 不足以证明宿主已全局发现。

关键适配：先明确可成立的主张与判准；每条材料承担具体论证职责；以证据约束主张范围；减少备赛流水账、无关自我削弱与结尾自我否定。正文至少一个真实可核实现象及一个可追溯学理时，必须解释“现象如何经学理支持本方论点”，不能只报理论名字或把假设当事实。真实性与用户原题优先，不隐藏足以改变结论的重要反证。
