# 已有 MiMo API Key：接入本 Skill 的操作步骤

本指南针对你已经拿到 Xiaomi MiMo API Key，想让一辩稿生成代码调用 `mimo-v2.6-pro-ultraspeed` 的场景。无需把 API Key 发给任何人，也不需要修改适配器源码。

## 先确认 API Key 来源

如果 Key 来自 **小米 MiMo API 开放平台**，使用以下官方配置：
- Base URL：`https://api.xiaomimimo.com/v1`
- Model ID：`mimo-v2.6-pro-ultraspeed`
- 协议：OpenAI Chat Completions 兼容协议
- Key 环境变量名：`MIMO_API_KEY`

如果 Key 来自第三方聚合平台，请使用该平台提供的 Base URL、模型标识和认证要求，不能直接假设官方小米地址可用。

注意：MiMo API Key 与 MiMo Token Plan 的 Key 不是同一种凭据，不能互换。UltraSpeed 模型的调用配额为定制服务；即使已有普通 MiMo API Key，也应确认账号已获该模型的访问权限。

官方入口：
- 模型接入示例：https://mimo.mi.com/models/zh-CN/mimo-v2.6-pro-ultraspeed
- API 首次调用：https://mimo.mi.com/docs/quick-start/first-api-call
- 模型 ID 列表：https://mimo.mi.com/docs/quick-start/model

## Windows PowerShell 操作步骤

### 1. 解压项目并进入根目录

进入解压后包含 `SKILL.md` 和 `model_api` 文件夹的项目目录。例如：

```powershell
cd "C:\你的路径\debatingskills"
```

### 2. 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r model_api/requirements.txt
```

如果 PowerShell 不允许激活虚拟环境，也可以直接用该环境的 Python 执行后续命令。

### 3. 创建本地配置文件

```powershell
Copy-Item model_api/config.example.yaml model_api/config.yaml
Copy-Item model_api/.env.example model_api/.env
```

`config.example.yaml` 只是模板；运行时要读取 `config.yaml`。

### 4. 放入 API Key

用文本编辑器打开 `model_api/.env`，填写：

```dotenv
MIMO_API_KEY=把你自己的真实API_KEY填在这里
```

不要加多余引号，不要把真实 Key 发到聊天里，也不要提交 `.env` 到 Git。

本项目 CLI 会从 `model_api/.env` 读取密钥；也可以直接在 PowerShell 当前会话设置：

```powershell
$env:MIMO_API_KEY = "你的真实API_KEY"
```

环境变量优先于 `.env` 中的同名变量。

### 5. 检查模型配置

打开 `model_api/config.yaml`，确认 `mimo` 配置段为：

```yaml
mimo:
  protocol: openai_chat
  base_url: https://api.xiaomimimo.com/v1
  api_key_env: MIMO_API_KEY
  model: mimo-v2.6-pro-ultraspeed
  max_tokens: 4096
  max_tokens_param: max_completion_tokens
  timeout_seconds: 180
```

并确认路由指向 MiMo：

```yaml
default_provider: mimo
roles:
  research_synthesis: mimo
  drafting: mimo
  review: mimo
```

如果你只希望一辩稿写作使用 MiMo、其他阶段仍使用别家模型，可以只设置 `drafting: mimo`，其余角色保留原来的 provider。

### 6. 先做配置检查（不会请求 API）

在项目根目录运行：

```powershell
python -m model_api.cli --config model_api/config.yaml --role drafting --provider mimo --prompt "测试" --dry-run
```

看到 `配置解析成功，未调用网络 API`，说明 YAML 路由配置正常，但还没有验证密钥和网络。

### 7. 发送真实测试请求

```powershell
python -m model_api.cli --config model_api/config.yaml --role drafting --provider mimo --prompt "请用中文回复：MiMo API 接入成功。" --max-tokens 256
```

成功时终端会显示模型回复，并在标准错误输出中显示 provider、model 和 response ID。

## 常见错误排查

- **401 / Unauthorized**：确认 Key 是否复制完整、是否属于 MiMo API 开放平台、是否已过期。
- **403 / 无权限**：确认账号是否获准调用 `mimo-v2.6-pro-ultraspeed`。官方说明 UltraSpeed 的 RPM/TPM 为定制服务。
- **404 / model not found**：确认 Model ID 是否精确为 `mimo-v2.6-pro-ultraspeed`；若使用第三方聚合平台，请使用它提供的模型名。
- **连接失败**：检查网络、代理及 Base URL；官方小米端点应为 `https://api.xiaomimimo.com/v1`。
- **429 / rate limit**：检查账号额度、并发限制及 UltraSpeed 服务权限。
- **配置文件找不到**：确认在项目根目录执行命令，且已将 `config.example.yaml` 复制为 `config.yaml`。

## 重要说明：API 接通不等于 Codex Skill 自动换模型

这套目录目前提供独立的 `ModelRouter` 与 CLI 调用入口。上述步骤能让该 Python 调用入口使用 MiMo API；它不会更改 ChatGPT/Codex 产品内部正在使用的模型。

如果要让某个自动化的一辩稿工作流全程使用 MiMo，需要让该工作流实际调用 `ModelRouter.generate(...)`（或 CLI），并将辩题、正反方、目标时长、已核验资料作为输入。Skill 的 `SKILL.md` 本身是工作流说明，不会仅因填写 API Key 就自动调用外部 API。


---

## 通用服务商接入教程

本文件保留 MiMo UltraSpeed 的具体配置示例。若你要接入 OpenAI/Codex、Claude/Opus、DeepSeek、Kimi 或火山方舟，请以 [`../references/api调用教程.md`](../references/api调用教程.md) 为统一操作指南。
