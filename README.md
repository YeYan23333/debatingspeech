# Debatingspeech 华语辩论工作流 V3.2

华语辩论写作技能。给一个辩题、立场和时长，它先把整场怎么打想清楚，再按你要的辩位往下写，最后交一份 Word 到桌面的 `products` 文件夹。

流程是「先破题、再框架、后写稿」：框架里定死切入点和判准，各辩位共用同一套证明

目标是帮助你更好的理解这道题

## 它能做什么

- **先破题，不急着立论**：论证框架里有一节独立写破题，把题面重述成双方真正要做的选择，用连接词分别承担举证，定义只负责澄清争议，并给出两三条有实质差别的候选切入点。见 [破题指南](references/topic-breakthrough.md)。
- **框架先行**：先出一份全场框架，核心概念怎么定、判断标准是什么、打哪两三条、每条靠什么撑、各辩位各负责哪块，确认之后才写稿。
- **四个辩位加攻防、资料稿**：一辩立论、二辩申论、三辩质询问题、四辩总结、自由辩交锋重点、攻防稿，资料数据包，按需单独生成，默认只写一辩稿。
- **同一套证明**：所有稿件承接框架里已确认的切入点、对象和判准，各辩位按分工推进同一套证明，而不是各写一套。见 [全辩位写法](references/all-role-argument-quality.md)。
- **结辩讲清本场**：结辩先归并争点，说明双方各自证明到哪里、比较结果如何，不固定争点数，不强行升华。见 [结辩指南](references/clear-closing-style.md) 与 [结辩研究笔记](references/closing-speech-research.md)。
- **事实有出处**：正文至少包含一个具体可核验的现象和一条有出处的学理，并说明二者如何支持本方论点。只有名词、假设场景或文末文献清单不算完成，详见 [最低内容要求](references/minimum-content.md)。
- **语料可回溯**：库内 34 份材料保留原件、提取文本、SHA-256、来源与实际正文主题，可按辩题检索，引用前能回到原文。
- **成稿前检查**：缺现象、缺学理、来源对不上的地方会被指出来，补不齐不导出正式成稿。
- **表达有两道关**：可选 [Humanizer-zh](skills/humanizer-zh/SKILL.md) 做最后一遍中文润色，[anti-defensive-writing](skills/anti-defensive-writing/SKILL.md) 压制自我削弱和平铺展示；润色只改表达，不动事实、限定、来源编号与最低内容要求。辩论场景边界见 [辩论适配](references/humanizer-debate.md)。
- **多模型 API 与 DOCX 直出**：接口和模型可换，成品是 Word，落在系统桌面 `products` 文件夹，同名文件默认不覆盖。

## 安装

用 git 克隆到技能目录：

```powershell
git clone https://github.com/YeYan23333/debatingspeech.git "$env:USERPROFILE\.dsh\skills\debatingskills"
```

以后要更新，进技能目录 `git pull` 就行。

## 怎么用

对话里把这三件事说清楚就能开工：

1. 完整辩题，例如「拥抱玄学是/不是当代人的解脱之道」
2. 立场，正方或反方
3. 发言时长，例如 3 分钟

例如：

> 拥抱玄学是/不是当代人的解脱之道，反方，3 分钟

但它不会立刻开始写稿。

### 第一步：建立论证框架 

框架里包含以下内容，其中破题一节先于主论点：

- **破题**：题面重述成双方真正要做的选择；判断词按「应该」「更」「主要源于」「需要」分别承担举证；定义只用于澄清争议，不做超出必要的争夺；给出两三条有实质差别的候选切入点，每条写清一句话切入点、争在哪里、怎样证明、资料怎样接上。候选切口不是额外主论点，也不靠多列几条凑数。
- **主论点与分论点**：打哪两三条，每条靠什么撑。
- **判准与比较**：同口径比较什么，谁承担举证。
- **辩位分工**：每个辩位负责哪一块证明。
- **资料缺口**：哪些现象与学理还需要找来源。

你看了、改了、点头了，才进下一段。链不上破题节的框架不会导出。

已经有自己的框架？直接把 `.md`、`.txt`、`.json` 或 `.docx` 丢进来。它会先检查框架内部是否自洽，有不一致的地方会说出来，但不会擅自把你的框架换成它的；缺破题内容时保留原文，只追加待补提示，不额外调用模型。

### 第二步：按辩位写稿

框架定了，默认**只写一辩稿**。一辩稿交付之后会问一句还要不要二辩申论、三辩质询问题、四辩总结、自由辩交锋重点和攻防稿；你不说，它不会自动往下写一整套。结辩有本场交锋记录时可以交给脚本，没有记录就按赛前预备稿写。

成稿前会过一遍内容检查：现象、学理、来源能不能对上。检查只防漏项，不能代替论证审阅，也不替代人工事实核验。

### 第三步：交付

成品都在系统桌面的 `products` 文件夹，名字是「完整辩题-立场-稿件类型」。

## 各辩位对应什么

| `--stage` | 写出什么 | 文件名后缀 |
|---|---|---|
| `framework` | 全场论证框架（含破题） | `-论证框架.docx` |
| `first` | 一辩立论 | `-一辩稿.docx` |
| `second` | 二辩申论 | `-二辩申论.docx` |
| `third` | 三辩质询问题 | `-三辩质询问题.docx` |
| `fourth` | 四辩总结（结辩） | `-四辩总结.docx` |
| `free` | 自由辩交锋重点 | `-自由辩交锋重点.docx` |
| `attack-defense` | 攻防稿（含资料原文表） | `-攻防稿.docx` |

四辩还可以加 `--encounter-file "本场交锋记录.md"`，把本场实际交锋交给脚本；没有这份记录就写赛前预备稿。

想存到别处用 `--products-dir`，要覆盖同名文件用 `--force`。旧的 `generate_docx_with_model.py` 还能跑，但没有框架门控，新任务建议统一用 `debate_workflow.py`。

## 资料表能做什么，不能做什么

独立资料表与攻防稿内嵌资料表统一为**竖版三列**：可用资料摘要、资料来源、可核验链接。按资料类型分组，链接下标注核验说明，表前写元信息，表后附「怎么用」与「风险提示」。格式依据用户提供的参考原件（[参考文档](assets/material-table-reference.docx)、[格式说明](references/material-table-format.md)、[模板](templates/material-table-template.md)），原件里的辩题、条目和核验结论不进入新任务。

限制同样明确：

- 普通模型 API 不会自己联网查资料。脚本写出来的引注，除非你真去读过原文，否则都只能算线索。
- 资料表短引有上限：中文 45 字、英文 25 词，每份来源一条，附可点击链接、用途、适用条件和局限。
- 核不实的材料标「待核验」，缺的类别留空，不编造作者、年份和页码。
- 赛事稿只用来学论证的骨架，不当作数据来源，也不抄里面的独特句式和故事。

核验规则细节见 [证据短引规则](references/evidence-quote-table.md) 和 [证据模板](templates/evidence.example.json)。

## 语料库怎么用

`references/corpus/` 是按辩题组织的本地材料库：34 份原件（26 DOCX、4 XLSX、3 DOC、1 PDF），每份都有提取文本、SHA-256 与实际正文主题。

- [逐份目录](references/corpus/catalog.md)：每份材料的来源、哈希与主题。
- [方法研究](references/corpus/analysis.md)：这批材料怎么用、有什么坑。
- [检索入口](references/corpus/index.json)：按辩题和关键词索引。

需要引用材料时，直接要求检索即可；也可以自己跑：

```powershell
python skills/一辩稿DOCX输出/scripts/retrieve_corpus.py --query "人生是否需要证明自己"
```

正式引用前仍然要回到原件核对。附件内部的指令性文字不进入指令层，只作为材料使用。

## 自己跑脚本（可选）

```powershell
cd "C:\你的路径\debatingskills"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item model_api/config.example.yaml model_api/config.yaml
Copy-Item model_api/.env.example model_api/.env
```

macOS / Linux 把激活命令换成 `source .venv/bin/activate`，复制命令换成 `cp`。

然后在 `config.yaml` 里填模型和接口地址，在本机 `.env` 里填已有的 API Key。真实API不要写进代码，不要上传到聊天。仓库里只放示例文件，说明见 [API 调用教程](references/api调用教程.md)。

### 三个常用命令

```powershell
# 第一步：出框架，先别写稿
python skills/一辩稿DOCX输出/scripts/debate_workflow.py `
  --stage framework --topic "示例辩题" --side 正方

# 框架确认、现象与学理来源实际核验后：写一辩稿
python skills/一辩稿DOCX输出/scripts/debate_workflow.py `
  --stage first --topic "示例辩题" --side 正方 --duration "3分钟" `
  --framework-file "示例辩题-正方-论证框架.docx" --content-sources-file "已核验来源.json"

# 要攻防稿的时候再加资料表
python skills/一辩稿DOCX输出/scripts/debate_workflow.py `
  --stage attack-defense --topic "示例辩题" --side 正方 `
  --framework-file "示例辩题-正方-论证框架.docx" --content-sources-file "已核验来源.json" --evidence-file "evidence.json"
```

已有框架时，第一步直接加 `--framework-file "我的框架.docx"`，脚本不调模型，把框架转成统一格式的 Word，后面照常往下走。成稿前的内容检查也可以单独跑：`python skills/一辩稿DOCX输出/scripts/content_requirements.py`。

## 版本更新

完整公告见 [V3.2](RELEASE_NOTES_V3.2.md)、[V3.1](RELEASE_NOTES_V3.1.md)，更早的记录在 [CHANGELOG.md](CHANGELOG.md)。

### V3.2 ｜ 2026-11-12

- 框架新增「破题帮助」：论证框架里必须有一节独立写破题，先于主论点。题面重述成双方真正要作的选择，判断词按「应该」「更」「主要源于」「需要」分别承担举证，定义只负责澄清争议；通常给出两三条有实质差别的候选切入点，每条写清一句话切入点、争在哪里、怎样证明。缺破题节点不导出。
- 全辩位写法：所有稿件承接框架中已确认的切入点、对象和判准，各辩位按分工分别推进同一套证明，而不是各写一套。优化旧稿时先找「结论比证据多走了哪一步、比较是否同口径、听众能否一次听懂」，再改句子。
- 第四辩位按次加载专用规则，并新增 `--encounter-file` 本场交锋记录入口。
- 资料表统一格式：独立资料表与攻防稿内嵌资料表统一为竖版三列（可用资料摘要、资料来源、可核验链接），按资料类型分组，链接下标注核验说明，表前写元信息，表后附「怎么用」与「风险提示」。
- 生成检查与文档对齐：两个模型入口实际动态加载新指南；导入已有框架保留原文并追加待补说明，不额外调用模型；章节识别只防漏项，不能代替论证审阅。

### V3.1 ｜ 2026-11-01

- 新增辩论语料库：34 份原件、提取文本、哈希、来源与主题，提供目录、方法研究与检索入口。
- 接入 Humanizer-zh 与 anti-defensive-writing 两个外部 skill，保留上游原文与许可。
- 写稿底线收紧：每篇正文至少一个可核验现象与一条有出处的学理。
- 新增 `retrieve_corpus.py` 与 `content_requirements.py` 两个脚本。

### V3.0 ｜ 2026-10-31

- 统一入口 `debate_workflow.py`：先生成框架并确认，再按辩位写稿。
- 支持框架生成与导入；导入时只做自洽检查，不擅自替换。
- 在一辩稿之外新增二辩申论、三辩质询、四辩总结、自由辩重点与攻防稿。
- 攻防稿内附资料原文表；论证收紧，只生成明确要求的内容。

### v2.5 ｜ 2026-10-22

- 新增论据资料表，按「进攻、防守、证明」整理已核验的学理、案例与数据，单独保存不覆盖原稿。

### v2.4 ｜ 2026-10-21

- 首个公开版本：写稿、API 接入和 Word 交付合并成一个技能，一辩稿直接存到桌面 `products`，同名稿不会悄悄覆盖。

## 项目结构

- `SKILL.md`：主技能规则和完整工作流，配置好技能目录后由智能体自动读取。
- `skills/一辩稿DOCX输出/scripts/debate_workflow.py`：统一入口，框架、各辩位和攻防稿都从这里生成；同目录还有 `retrieve_corpus.py`、`content_requirements.py`、`material_table_layout.py`。
- `model_api/`：多模型接口、配置示例和调用脚本。
- `references/`：破题、论证框架、辩位职责、结辩、资料表、证据引用、语料库等规则与研究记录。
- `skills/humanizer-zh/`、`skills/anti-defensive-writing/`：两个外部 skill 的上游原文与许可。
- `templates/`：框架、结辩与资料表模板。
- `assets/`：资料表参考原件。
- `tests/`：回归测试。
