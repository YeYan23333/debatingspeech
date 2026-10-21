# debatingspeech 一辩稿生成器

华语辩论一辩稿写作skills：给出辩题、立场和时长，生成几乎完整的中文一辩稿，并把文件存到桌面。

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

填写以下三项内容以开始生成：

1. 完整辩题，例如「童话是/不是梦」
2. 立场，正方或反方
3. 发言时长，例如 3 分钟

例如：

> 童话是/不是梦，反方，3分钟

随后会拿到完整的一辩稿正文、正文篇幅与预计口播时间、文末编号引注对应的来源，以及一份 Word 文件。

成品保存在系统桌面的 `products` 文件夹，文件名就是完整辩题加立场，例如 `童话是不是梦-反方-一辩稿.docx`。同名稿默认不覆盖。

想改稿直接说改哪里，不用重复辩题和立场。

## 可选：接入模型 API

DSH和豆包这类专用大模型只能调用自家的模型
如果想让自带脚本直接调用模型生成初稿：

```powershell
pip install -r requirements.txt
```

再按 [API 调用教程](references/api调用教程.md) 配置 `model_api/config.yaml` 与本机 `.env`。
## 版本更新公告

### v2.5 ｜ 2026-10-22

**更新内容**

- 新增论据资料表：稿子交付后，可把本次核验过的学理、案例与数据按“进攻、防守、证明”整理成备赛表。
- 每条注明用途、适用条件、核对结果与来源；未核实的不收录，缺类留空。
- 资料表单独保存，不覆盖原稿，不写入正文。

**用法**

- 稿子保存后按提示回「要」生成，回「不用」跳过。
- 表与一辩稿同在 `products` 文件夹，文件名为「辩题-立场-论据资料表」。
- 已安装的版本执行 `git pull` 更新。

### v2.4 ｜ 2026-10-21

**更新内容**

- 首个公开版本：写稿、API 接入与 Word 交付合并为一个技能。
- 修复偶现的「短剧腔」行文，论证衔接更顺。
- 一辩稿存入桌面 `products`，保留完整辩题，同名不覆盖。

**用法**

- 给出辩题、立场与时长即可开始，缺项追问，已给的不重复问。
- 需模型直出时按 [API 调用教程](references/api调用教程.md) 配置；不配置也能正常写稿。

