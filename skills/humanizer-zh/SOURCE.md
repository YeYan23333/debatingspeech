# Humanizer-zh 上游来源与接入记录

- 用户指定仓库：https://github.com/op7418/Humanizer-zh?tab=readme-ov-file
- 分支：main；当前 HEAD 未通过 API 确认，不填写提交号。
- Skill：https://raw.githubusercontent.com/op7418/Humanizer-zh/main/SKILL.md
- README：https://raw.githubusercontent.com/op7418/Humanizer-zh/main/README.md
- 许可：https://raw.githubusercontent.com/op7418/Humanizer-zh/main/LICENSE
- 读取日期：2026-10-31（Asia/Shanghai）
- 获取方式：web 工具读取完整 raw 文本，按工具显示的行号完整性检查后保存；SKILL 390 行、README 132 行、LICENSE 19 行。内容按可见文本保留，未确认上游原始字节或文件哈希。本文的本地 SHA256 只用于本地文件一致性，不冒充上游 blob hash。
- 原文版本标识：SKILL frontmatter `metadata.revision: "2026-09-23"`。完整包含 A–F 六类、31 个编辑检查点、编辑保真优先级与来源声明。
- 许可：MIT；版权 `Copyright (c) 2026 歸藏`。原文许可完整保存在同目录 LICENSE。
- README 原样文本另存为 upstream-README.md，以免误作本地安装说明。

## 已检查的依赖与路由

SKILL.md 只引用上游外部来源链接，没有必需的相对路径、脚本、图片或运行时依赖。README 的 CHANGELOG.md、tests/README.md 是上游说明与验证材料的链接，不是执行该技能的依赖；本地未复制这些额外材料，也没有执行 npx、git clone 或上游代码。

用户指定的 GitHub 根网页返回了旧缓存（24 类清单），raw SKILL 与 raw README 及 GitHub 的 SKILL 文件页相互一致，已更新为 31 个检查点。本快照以 raw 文件内容为准。

## 辩论工作流的接入方式

建议保存为包内 `skills/humanizer-zh/SKILL.md`，在主 skill 中指定为成稿后的自然表达编辑环节，并在模型 API 提示词中实际加载完整规则。独立全局发现仍需按根任务的授权范围安装到宿主技能目录；包内文件存在不代表已全局安装。

适配顺序：确认框架和事实材料 → 起草并落实至少一个现象及一个学理 → 按 anti-defensive-writing 整理主线 → 用 Humanizer-zh 编辑自然表达 → 再核对现象、学理、出处及限定是否保留。若两份写作规则冲突，事实、原题、已确认框架、确定程度和真实归因优先；例如不能因 anti-defensive-writing 的禁用词建议删掉承担数量含义的“仅”或具有必要限制作用的句子。

该环节保留辩论口播需要的有意排比、真实比较和短句，不机械删连接词，不把所有文本改成同一种腔调；只改确实空泛、重复、歧义或不合文体的表达。不补造第一人称经历、数字、专家身份和来源，不删现象/学理来追求简短，不把“可能”改成“必然”。不判断作者身份，不承诺检测器分数或绕过 AI 检测。
