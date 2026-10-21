# Provider Matrix：服务商、产品与 API 协议对应表

本表里的 `provider` 是本项目配置文件中的路由别名，`protocol` 是请求协议适配器，`model` 是服务商侧模型标识。三者不可混为一谈。

| 配置别名 | 服务商 | 产品/API 接口 | `protocol` | 必须确认的配置 |
|---|---|---|---|---|
| `codex` | OpenAI | OpenAI Responses API（不是本地 Codex CLI） | `openai_responses` | OpenAI API Key、可用 Responses 模型 ID |
| `claude` | Anthropic | Anthropic Messages API / Claude | `anthropic_messages` | Anthropic API Key、Claude 模型 ID |
| `claude_opus` | Anthropic | Anthropic Messages API / Claude Opus | `anthropic_messages` | Anthropic API Key、Opus 模型 ID |
| `mimo` | 小米 | Xiaomi MiMo API | `openai_chat`（兼容格式） | MiMo Base URL、模型 ID、token 参数 |
| `deepseek` | DeepSeek | DeepSeek API | `openai_chat`（兼容格式） | DeepSeek Base URL、模型 ID |
| `kimi` | Moonshot AI / Kimi | Moonshot / Kimi API | `openai_chat`（兼容格式） | 账户区域对应的 Base URL、模型 ID |
| `volcengine` | 火山引擎 | 火山方舟 Ark API | `openai_chat`（兼容格式） | 区域 Base URL、模型名或 Endpoint ID |
| `openai_chat` | OpenAI | OpenAI Chat Completions API | `openai_chat` | OpenAI API Key、可用 Chat 模型 ID |

## 对应官方文档

- OpenAI Responses API: https://platform.openai.com/docs/api-reference/responses
- OpenAI Chat Completions API: https://platform.openai.com/docs/api-reference/chat
- Anthropic Messages API: https://docs.anthropic.com/en/api/messages
- DeepSeek API: https://api-docs.deepseek.com/zh-cn/
- Xiaomi MiMo API: https://platform.xiaomimimo.com/docs/zh-CN/
- Moonshot AI / Kimi API: https://platform.moonshot.ai/docs/guide/prompt-best-practice
- Volcano Engine Ark API: https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh

> 这是适配器映射，不是对所有型号、所有可选参数或所有账号权限的兼容保证。调用前请以官方文档及控制台显示为准。
