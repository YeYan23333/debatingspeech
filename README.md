# debatingskills

主技能名为 `debatingspeech`。写稿、API 接入与 DOCX 交付已合并到唯一的 `SKILL.md`，不再安装多个子技能。详细教程与研究记录放在 references 中，按需读取，不必全部粘贴进输入框。

## 安装与使用

仓库根目录就是技能目录，克隆后文件夹名正好与 `SKILL.md` 的 name 一致：

```powershell
git clone https://github.com/YeYan23333/debatingspeech.git "$env:USERPROFILE\.dsh\skills\debatingspeech"
```

macOS/Linux 用 `git clone https://github.com/YeYan23333/debatingspeech.git ~/.dsh/skills/debatingspeech`。也可以解压发行包，将整个目录复制到你的技能目录并命名为 `debatingspeech`；保留配套脚本和参考文件，勿只复制 SKILL.md。原有常用安装示例为 `~/.codex/skills/debatingspeech/`；已有项目环境继续使用其配置的技能目录即可。

新对话开场简短说明可写改一辩稿、核验学理案例、生成Word，以及帮助接入API并做连通性测试，再给出写稿三要点：完整辩题、正方或反方、发言时长。已有信息不重复询问；明确的API任务直接处理。

调用 `$debatingspeech` 开始。最终默认交付Word DOCX：

`<系统实际桌面>/products/<用户实际辩题>-正方或反方-一辩稿.docx`

实际文件名如 `嗑CP热潮折射出人们对爱情的更深信仰-正方-一辩稿.docx`。生成时自动在实际桌面创建products并直接放入文件，不再使用辩题子目录；技能包内products目录已去掉。支持桌面重定向到其他盘符，保留完整辩题命名及同名稿防覆盖。

保存并重新打开检查成功后，显示：

“请在桌面上的products文件夹中检查，如不满意请继续提出您的修改意见，我将继续为您修改”

该提示不写入DOCX，预览或失败不显示成功。若显式指定其他输出目录，提示实际位置。

## 语言与证据

减少“真正要回答的是……”等套句，以及反复“不是……而是……”的对照。用具体对象、条件、动作与后果讲清论证，按语义拆长句，证据后有解释；不写预设反驳。每篇必须至少1条学理及1个已核验真实案例，通常安排1–2条学理与1–2例。学理清楚简洁、直接解释关键机制；案例真实且能支持论点。学理说明与案例叙述可分别约占正文20%–30%，其余留给本方推理、界定与收束，按正文自然统筹。学理、实例和数据都有正文编号引注及文末可点击出处；资料不足时保留缺口，不编造学说、故事或来源。正文先补足类别归属与共同机制，再用“XX作为YY的一种具体表现，展现其Z特质”等方式连贯说明支持关系；逻辑不成立时调整论点或材料，不在口播中堆审稿式退让句。

用户可见进度只简述逻辑或证据缺口，不输出内部思考链和检索渠道日志；最终参考文献仍完整保留。常规交付不附比赛渠道报告。自然口播规范见 [表达指南](references/natural-first-speaker-style.md)，材料范围见 [样本记录](references/style-sample-notes.md)。

## 语速与正文长度

默认310–340字/分钟，初稿参考325字/分钟；标题、元信息、编号引注和参考文献不计入正文。

| 发言时长 | 正文目标 | 初稿参考 |
|---|---:|---:|
| 1分钟 | 310–340字 | 325字 |
| 2分30秒 | 775–850字 | 约813字 |
| 3分钟 | 930–1020字 | 975字 |
| 3分30秒 | 1085–1190字 | 约1138字 |
| 自定义 | 分钟数×310–340 | 分钟数×325 |

## API 与 DOCX

安装依赖：`pip install -r requirements.txt`。按 [API调用教程](references/api调用教程.md) 配置 `model_api/config.yaml` 与本机环境变量或 `model_api/.env`；已有配置保留。不要把真实密钥发到聊天或提交到源码仓库。

已有稿件转换：

`python skills/一辩稿DOCX输出/scripts/export_to_docx.py --topic "实际辩题" --side 正方 --input "临时稿件.txt"`

已配置模型生成：

`python skills/一辩稿DOCX输出/scripts/generate_docx_with_model.py --topic "实际辩题" --side 正方 --duration "3分钟" --context-file "research-notes.txt"`

资料文件分开写已核验事实、真实实例及来源、仅供表达参考的样稿。生成脚本向所有配置的 provider 传入同一表达指南与时长字数预算，不增加额外模型调用。添加 `--dry-run` 可做离线配置、指南和路径检查，不代表网络或密钥已经验证。普通文本 API 不自动联网搜索。

详细 [DOCX输出说明](references/docx-output.md)、[API接口说明](model_api/README.md) 和 [赛事来源索引](references/tournament-source-catalog.md) 均按需读取。赛事索引区分官方入口、社区转写和本轮访问范围，不是已经下载核验的完整比赛库。

## 目录与离线测试

唯一技能入口为根目录SKILL.md；references保存表达、教程及来源索引；model_api保存适配器、配置与原有测试；skills/一辩稿DOCX输出/scripts保留兼容的生成和转换脚本；成品保存在系统桌面的products；tests保存输出及规则回归测试。

在项目根目录运行：

`python -m unittest discover -s model_api/tests -v`

`python -m unittest discover -s tests -v`
