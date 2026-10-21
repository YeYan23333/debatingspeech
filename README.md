# debatingspeech

华语辩论一辩稿写作技能：给出辩题、立场和时长，生成可以直接口播的中文一辩稿，并把 Word 文件存到桌面。

## 安装

仓库根目录就是技能目录，克隆后文件夹名正好与 `SKILL.md` 的 name 一致：

```powershell
git clone https://github.com/YeYan23333/debatingspeech.git "$env:USERPROFILE\.dsh\skills\debatingspeech"
```

macOS / Linux：

```bash
git clone https://github.com/YeYan23333/debatingspeech.git ~/.dsh/skills/debatingspeech
```

也可以下载压缩包，解压后把整个目录放到技能目录并命名为 `debatingspeech`。请保留全部脚本和 `references`，不要只复制 `SKILL.md`。换用其他 Agent 软件时，放进它自己的技能目录即可，例如 `~/.codex/skills/debatingspeech`。

## 使用

把三件事说清楚就行：

1. 完整辩题，例如「童话是/不是梦」
2. 立场，正方或反方
3. 发言时长，例如 3 分钟

例如：

> 童话是/不是梦，反方，3分钟

随后会拿到完整的一辩稿正文、正文篇幅与预计口播时间、文末编号引注对应的来源，以及一份 Word 文件。

成品保存在系统桌面的 `products` 文件夹，文件名就是完整辩题加立场，例如 `童话是不是梦-反方-一辩稿.docx`。同名稿默认不覆盖。

想改稿直接说改哪里，不用重复辩题和立场。

## 可选：接入模型 API

如果想让自带脚本直接调用模型生成初稿：

```powershell
pip install -r requirements.txt
```

再按 [API 调用教程](references/api调用教程.md) 配置 `model_api/config.yaml` 与本机 `.env`。仓库里只放示例文件，真实密钥不会上传。

## 目录

| 路径 | 说明 |
|---|---|
| `SKILL.md` | 技能入口 |
| `references/` | 表达指南、赛事来源索引与教程 |
| `model_api/` | 模型适配器与配置示例 |
| `skills/一辩稿DOCX输出/scripts/` | 导出与生成脚本 |
| `tests/` | 回归测试 |

## 反馈

问题或改进建议，欢迎提 Issue 或 PR。
