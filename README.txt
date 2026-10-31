Debatingspeech 华语辩论工作流 V3.0

本技能用于华语辩论稿件写作。输入辩题、立场与发言时长后，先生成全场论证框架，确认后再按辩位成稿，最终以 Word 文件保存至系统桌面【products】文件夹。

与上一版相比，生成流程由单一的一辩稿改为框架先行、按辩位分步生成。


安装

将仓库克隆到技能目录：

    git clone https://github.com/YeYan23333/debatingspeech.git "$env:USERPROFILE\.dsh\skills\debatingskills"

仓库名为【debatingspeech】，技能名与目录名为【debatingskills】，克隆时将目标路径指定为【debatingskills】即可，无需安装后改名。Codex 使用 ~/.codex/skills/debatingskills；macOS 与 Linux 路径结构相同，仅家目录写法不同。

更新时在技能目录执行 git pull。

仓库内的【references】、【templates】、【skills】、【model_api】均需保留，仅取【SKILL.md】会导致功能缺失。


使用

对话中提供三项信息：

1. 完整辩题，例如「童话是/不是梦」；
2. 立场，正方或反方；
3. 发言时长，例如 3 分钟。

示例：

    童话是/不是梦，反方，3 分钟

技能不会直接开始写稿。第一步输出全场论证框架，包括核心概念如何界定、判断标准、主要交锋、各辩位分工。框架确认或修改后，进入写稿环节。

已有框架的，可直接提供【.md】、【.txt】、【.json】或【.docx】文件。导入前会检查框架内部是否自洽，指出不一致之处，不替换原有框架。

框架确定后，默认只生成一辩稿。一辩稿交付后，询问是否需要二辩申论、三辩质询问题、四辩总结、自由辩交锋重点与攻防稿；未收到明确要求时不生成其余稿件。

各辩位共用同一套立场、判断标准与核心论点。

成品保存于系统桌面【products】文件夹，命名格式为「完整辩题-立场-稿件类型」：

    桌面/products/
    ├── 童话是不是梦-反方-论证框架.docx
    ├── 童话是不是梦-反方-一辩稿.docx
    ├── 童话是不是梦-反方-二辩申论.docx
    ├── 童话是不是梦-反方-三辩质询问题.docx
    ├── 童话是不是梦-反方-四辩总结.docx
    ├── 童话是不是梦-反方-自由辩交锋重点.docx
    └── 童话是不是梦-反方-攻防稿.docx

以上仅为命名示例，不代表一次生成全部稿件。同名文件默认不覆盖；修改稿件时直接说明修改位置，无需重复提供辩题与立场。


执行脚本（可选）

不安装 Python 也可通过对话完成写作。需直接调用模型生成初稿时，按以下步骤配置。

    cd "C:\你的路径\debatingskills"
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Copy-Item model_api/config.example.yaml model_api/config.yaml
    Copy-Item model_api/.env.example model_api/.env

macOS 与 Linux 将激活命令替换为 source .venv/bin/activate，复制命令替换为 cp。

在【config.yaml】中填写模型与接口地址，在本机【.env】中填写 API Key。密钥不得写入代码、不得上传至对话或提交至 Git。仓库内仅提供示例文件，说明见【references/api调用教程.md】。


常用命令

生成框架：

    python skills/一辩稿DOCX输出/scripts/debate_workflow.py --stage framework --topic "示例辩题" --side 正方

框架确认后生成一辩稿：

    python skills/一辩稿DOCX输出/scripts/debate_workflow.py --stage first --topic "示例辩题" --side 正方 --duration "3分钟" --framework-file "示例辩题-正方-论证框架.docx"

生成攻防稿并附资料表：

    python skills/一辩稿DOCX输出/scripts/debate_workflow.py --stage attack-defense --topic "示例辩题" --side 正方 --framework-file "示例辩题-正方-论证框架.docx" --evidence-file "evidence.json"

已有框架时，第一步直接加 --framework-file "我的框架.docx"，脚本不调用模型，将框架转换为统一格式的 Word 文件，后续流程不变。

模型由【config.yaml】中的 default_provider 指定，临时切换用 --provider。--dry-run 仅检查参数与目标路径，不代表接口可用。


辩位与文件命名

 · framework：全场论证框架，后缀【-论证框架.docx】
 · first：一辩立论，后缀【-一辩稿.docx】
 · second：二辩申论，后缀【-二辩申论.docx】
 · third：三辩质询问题，后缀【-三辩质询问题.docx】
 · fourth：四辩总结，后缀【-四辩总结.docx】
 · free：自由辩交锋重点，后缀【-自由辩交锋重点.docx】
 · attack-defense：攻防稿（含资料原文表），后缀【-攻防稿.docx】

输出目录用 --products-dir 指定，覆盖同名文件用 --force。旧脚本【generate_docx_with_model.py】仍可使用，但无框架确认环节，新任务统一使用【debate_workflow.py】。


资料表的边界

 · 普通模型 API 不联网检索。脚本输出的引注未经原文核对，只能视为线索。
 · 资料短引有长度上限：中文 45 字、英文 25 词，每份来源一条，附可点击链接、用途、适用条件与局限。
 · 无法核实的材料标注「待核验」，缺失类别留空，不编造作者、年份与页码。
 · 赛事稿仅用于参考论证结构，不作为数据来源，不复制其中的独特句式与事例。

核验规则见【references/evidence-quote-table.md】与【templates/evidence.example.json】。


版本更新公告

V3.0 ｜ 2026-10-31

Debatingspeech 华语辩论工作流 V3.0 版本更新公告

很荣幸，经过各位使用者的反馈与迭代打磨，华语辩论写作技能 debatingskills 迎来第三个大版本的正式更新（V3.0）。

自 v2.5 发布以来，使用场景已从单一的一辩稿撰写逐步扩展到整场备赛。本次更新在保留原有写稿、接口与交付能力的基础上，将生成流程重构并补齐多个辩位的成稿能力，进一步提升备赛流程的完整性与稿件之间的一致性，接下来它将迎来更加连续的思考流程。我们对此次更新非常兴奋，因此本次更新迎来了新的大版本号：V3.0。

更新内容

1. 新增统一辩论工作流
引入统一入口 debate_workflow.py，调整生成流程为：先生成全场论证框架并交由使用者确认，确认后再按需生成对应辩位的稿件。各辩位共用同一套立场、判断标准与核心论点，避免不同稿件之间出现论证偏移。

2. 支持框架生成与导入
论证框架既可由技能自动生成，也可由使用者提供文件直接导入。导入时脚本会先检查框架内部是否自洽，指出不一致之处，不会擅自替换使用者原有的框架。

3. 扩展辩位覆盖范围
在一辩立论之外，新增二辩申论、三辩质询问题、四辩总结、自由辩交锋重点与攻防稿五类稿件，支持按辩位单独生成。各辩位遵循独立的写作职责。

4. 攻防稿附资料原文表
攻防稿文内附可用资料原文表，逐条列明资料用途、可能适用的交锋、原文短引、作者与标题及时间、可点击原文链接与适用局限。

5. 论证进一步收紧
围绕最强且切题的主张组织论证，不主动增加无关的举证负担，不写备赛流水账，不平铺展示，并减少机械套路化表达，保持自然叙述。

6. 仅生成明确要求的内容
默认只生成一辩稿。一辩稿交付后提示可扩展的稿件类型，未收到明确要求时不自动生成整套稿件。

7. 延用原有交付方式
保留多模型 API 接入、Word DOCX 直出桌面“products”文件夹、同名稿件防覆盖，以及旧版论据资料表与兼容脚本。

使用说明

1. 在对话中给出完整辩题、立场与发言时长三项信息，技能将先生成全场论证框架，确认后再进入写稿环节。

2. 已有论证框架的，可直接提供 .md、.txt、.json 或 .docx 文件，无需重新生成。

3. 一辩稿交付后，按提示回复需要生成的辩位；回复「不需要」即结束，不生成其余稿件。

4. 成品统一保存在系统桌面的 products 文件夹内，文件命名格式为「完整辩题 - 立场 - 稿件类型」，同名文件默认不覆盖。

5. 如需自行调用脚本，在项目根目录执行 --stage framework 生成框架，确认后执行 --stage first 生成一辩稿，其余辩位使用 second、third、fourth、free、attack-defense。

6. 已安装旧版本的用户，在技能目录下执行 git pull 指令，即可更新至 V3.0。

v2.5 ｜ 2026-10-22

更新内容

 · 新增论据资料表：稿件交付后，可将本次核验过的学理、案例与数据按“进攻、防守、证明”整理为备赛表。
 · 每条注明用途、适用条件、核对结果与来源；未核实的不收录，缺失类别留空。
 · 资料表单独保存，不覆盖原稿，不写入正文。

用法

 · 稿件保存后按提示回复「需要」生成，回复「不需要」跳过。
 · 文件名为「辩题-立场-论据资料表」，与成稿同存于【products】文件夹。

v2.4 ｜ 2026-10-21

首个公开版本：写稿、API 接入与 Word 交付合并为一个技能；一辩稿直接保存至桌面【products】，同名稿不覆盖。

更早的改动见【CHANGELOG.md】。


项目结构

 · 【SKILL.md】：主技能规则与完整工作流，配置技能目录后由智能体自动读取。
 · 【skills/一辩稿DOCX输出/scripts/debate_workflow.py】：V3.0 统一入口，框架、各辩位与攻防稿均由此生成。
 · 【model_api】：多模型接口、配置示例与调用脚本。
 · 【references】：论证框架、辩位职责、证据引用、自然口播等规则。
 · 【templates】：框架模板与资料表示例。
 · 【tests】：回归测试。
