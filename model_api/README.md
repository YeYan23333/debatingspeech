# 多模型 API 接口层

该目录为 `debatingskills` 项目的 `debatingspeech` 主 Skill 提供一个可替换的 Python API 调用层。核心目标是把“论证工作流”与“模型服务商”解耦。

## 当前适配协议

| 协议 | 典型用途 | 已预留适配器 |
|---|---|---|
| `openai_responses` | OpenAI Responses API；账户允许时用于 Codex 相关模型/工作流 | `OpenAIResponsesProvider` |
| `openai_chat` | OpenAI Chat Completions 兼容 API，例如可配置的 DeepSeek、MiMo、Kimi、火山方舟等 | `OpenAICompatibleChatProvider` |
| `anthropic_messages` | Claude / Opus 的 Anthropic Messages API | `AnthropicMessagesProvider` |

不是每家服务的所有模型都支持同一协议、参数或功能。配置中的 `base_url`、模型 ID、token 参数及可选 `extra_body` 必须以目标服务当前官方文档为准。

## 接口协议与服务商对应关系

这里必须区分**服务商/模型名称**和**API 请求协议**。配置中的 `protocol` 是代码调用的协议适配器；它不等于某一家厂商的专属产品名称。

| 配置中的 `protocol` | 代码适配器 | 对应服务商 / 产品 | 配置注意事项 |
|---|---|---|---|
| `openai_responses` | `OpenAIResponsesProvider` | OpenAI Responses API；可用于账户支持的 OpenAI 模型。`codex` 只是本项目中的配置别名，不代表启动本地 Codex CLI | OpenAI API Key；使用账户可调用的模型 ID |
| `anthropic_messages` | `AnthropicMessagesProvider` | Anthropic 原生 Messages API；Claude、Claude Opus | Anthropic API Key；使用账户可调用的 Claude 模型 ID |
| `openai_chat` | `OpenAICompatibleChatProvider` | OpenAI Chat Completions API，以及明确兼容该格式的 DeepSeek、MiMo、Moonshot/Kimi、火山方舟等配置 | 必须核对各家 Base URL、模型 ID、token 参数和可选字段 |

### 代码中接口的位置

- `SUPPORTED_PROTOCOLS`：协议白名单，说明代码认可哪几类请求协议。
- `OpenAIResponsesProvider`：**OpenAI Responses API** 适配器；不是本地 Codex CLI 执行器。
- `AnthropicMessagesProvider`：**Anthropic Messages API** 适配器，面向 Claude / Opus。
- `OpenAICompatibleChatProvider`：**OpenAI Chat Completions 格式**适配器，可按 `base_url` 配置为不同服务商。它不是“所有服务商都是 OpenAI API”，只是复用兼容的请求格式。
- `model_api/config.example.yaml`：每个服务商配置块顶部都注明“服务商 / 产品接口 / 本项目协议 / 官方文档”。以 `base_url`、`api_key_env` 和 `model` 三项确定实际调用目标。

### 各服务商配置块与官方文档

- **OpenAI Responses API**：https://platform.openai.com/docs/api-reference/responses
- **OpenAI Chat Completions API**：https://platform.openai.com/docs/api-reference/chat
- **Anthropic Messages API（Claude / Opus）**：https://docs.anthropic.com/en/api/messages
- **DeepSeek API**：https://api-docs.deepseek.com/zh-cn/
- **Xiaomi MiMo API**：https://platform.xiaomimimo.com/docs/zh-CN/
- **Moonshot AI / Kimi API**：https://platform.moonshot.ai/docs/guide/prompt-best-practice
- **Volcano Engine Ark API**：https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh

官方文档、可用模型名、区域地址和请求字段会更新。以上链接是核对入口，接入前应确认具体账户和模型的当前要求；不应把某个示例模型 ID 当作长期固定值。

## 已有 MiMo API Key：按步骤接入

请先看 [`CONNECT_EXISTING_MIMO_API.md`](CONNECT_EXISTING_MIMO_API.md)，其中包含 Windows PowerShell 命令、配置片段、测试命令和常见错误排查。

## 快速配置

```bash
cd debatingskills
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r model_api/requirements.txt
cp model_api/config.example.yaml model_api/config.yaml
cp model_api/.env.example model_api/.env
```

然后编辑 `model_api/config.yaml` 中的模型 ID、Base URL 和角色路由，并将真实 API Key 写入 `model_api/.env`。`.env` 和 `config.yaml` 已列入 `.gitignore`，不要把密钥提交到版本控制。

先执行不联网的配置检查：

```bash
python -m model_api.cli --config model_api/config.yaml --role drafting \
  --prompt "只回复：配置检查通过" --dry-run
```

确认配置和环境变量后，再发起实际调用：

```bash
python -m model_api.cli --config model_api/config.yaml --role drafting \
  --prompt "请说明一辩稿的主张—机制—证据—解释结构。"
```

Windows PowerShell 可以将命令写在一行，避免 shell 换行差异。

## 多模型路由

`config.yaml` 中的 `roles` 可把不同工作阶段分配给不同 provider：

```yaml
default_provider: deepseek
roles:
  research_synthesis: deepseek
  drafting: claude_opus
  review: mimo
```

- `research_synthesis`：只综合已检索到的资料与链接；本适配器本身不会自动联网搜索。
- `drafting`：根据用户立场、时长和核验过的证据写稿。
- `review`：检查逻辑链、篇幅、口播自然度、引用编号与参考文献对应关系。

调用时可以用 `--provider` 临时覆盖配置路由。API 输出必须视为待核验草稿；模型不能代替来源核查。

## 在代码中调用

```python
from model_api.providers import ModelRouter, load_config

config = load_config("model_api/config.yaml")
router = ModelRouter(config)

result = router.generate(
    role="drafting",
    system_prompt="你是华语辩论一辩稿写作助手。",
    user_prompt="请根据以下已核验资料生成一篇3分钟反方一辩稿……",
    max_tokens=4096,
)
print(result.text)
```

如果需要强制指定某一家：

```python
result = router.generate(
    role="drafting",
    provider_override="kimi",
    system_prompt="你是严谨的辩论稿编辑。",
    user_prompt="请检查正文中每条证据是否支撑对应主张。",
)
```

## 新增服务商

1. 若服务商兼容 OpenAI Chat Completions，只需在 YAML 新增 `openai_chat` 配置。
2. 若兼容 OpenAI Responses API，使用 `openai_responses`。
3. 若使用 Anthropic Messages API，使用 `anthropic_messages`。
4. 若协议不兼容以上三种，在 `providers.py` 实现新的适配器，遵循 `generate(system_prompt, user_prompt, max_tokens) -> ModelResult`，并在 `create_provider` 工厂注册新协议。
5. 如果供应商的工具调用、联网搜索、文件输入或推理参数具有专用格式，应写独立扩展，不要假设通用文本接口已经支持这些功能。

## 安全与运行限制

- API Key 只从环境变量读取；代码不会打印密钥。
- 不要将真实密钥写进 YAML、Python 代码、聊天提示或 Git 仓库。
- 调用会产生服务商费用；`--dry-run` 只检查配置，不会请求模型。
- 当前适配器只实现普通文本请求/响应，不实现流式输出、工具调用、联网搜索、图像/文件输入、重试、计费追踪或自动故障切换。
- 模型名称、API 路径、区域、账户权限和参数兼容性会变化，接入前请核对官方文档。
- 没有 API Key 的环境无法进行真实模型连通性测试。本包的单元测试只检查配置校验和路由逻辑。

## 官方文档入口

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [DeepSeek API（OpenAI / Anthropic 兼容说明）](https://api-docs.deepseek.com/zh-cn/)
- [Xiaomi MiMo API 文档](https://platform.xiaomimimo.com/docs/zh-CN/)
- [Moonshot / Kimi API 文档](https://platform.moonshot.ai/docs/guide/prompt-best-practice)
- [火山方舟兼容 OpenAI SDK](https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh)
