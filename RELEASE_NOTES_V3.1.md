# debatingspeech V3.1 ｜ 2026-11-01

这一版补的是**稿子里的事实从哪来**。V3.0 解决「先搭框架、再按辩位拆稿」，V3.1 让每个事实都能追到出处。

## 语料入库

- 两批附件共 **34 份有效材料**入库（13 份独立 DOCX + 短视频 ZIP 内 21 份），排除 2 个 Office 锁文件。
- 每份保留原件、提取文本、SHA-256、来源与实际正文主题；所有事实状态仍标「未独立核验」。
- 新增 `references/corpus/`：逐份目录 `catalog.md`、方法研究 `analysis.md`、按辩题检索入口 `index.json`。

## 两个外部 skill 接入

- **Humanizer-zh**（MIT，保留上游与许可）：成稿后的最后一遍中文表达润色，只动表达，不动事实、必要限定、来源编号与最低内容要求。辩论场景的边界见 `references/humanizer-debate.md`。
- **anti-defensive-writing**：反向压制防御性写作，落到辩论语境见 `references/debate-anti-defensive-writing.md`。

## 更硬的写稿底线

- 正文至少一个**具体现象**加一条**学理**，并说明两者如何互相支持；缺项或来源未确认不导出正式成稿。
- 框架、提示词、模板与成稿检查同步收紧。
- 新增 `retrieve_corpus.py`（按辩题检索语料）与 `content_requirements.py`（成稿前强制检查）。

## 兼容

原有 API 接入、桌面 `products` 直出、同名不覆盖、论据资料表全部保留。

**完整改动**：44 → 134 个文件，新增 89 个、修改 17 个，另补一份本公告。
