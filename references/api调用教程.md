
# API 调用教程

## 目标

本教程 面向**已经拥有某家模型 API Key**的用户，帮助其将 API 接入
`model_api/` 代码层，并配置一辩稿生成、资料综合和审稿任务使用的模型。

本教程不要求用户把 API Key 发给助手，也不要求把密钥写入 Python
代码。真实 Key 只应放在本机环境变量或本机 `.env` 文件中。

## 核心概念

-   **服务商**：例如 OpenAI、Anthropic、小米
    MiMo、DeepSeek、Moonshot/Kimi、火山引擎。
-   **API 协议**：代码如何组织请求，例如
    `openai_responses`、`anthropic_messages`、`openai_chat`。
-   **模型 ID**：服务商 API
    接受的具体模型标识，必须以账户权限和当前官方文档为准。
-   **Base URL**：API 服务入口。官方直连与第三方聚合平台的地址可能不同。
-   **API Key 环境变量**：代码从哪个环境变量读取密钥，例如
    `MIMO_API_KEY`。这只是变量名，不是密钥本身。

## 支持的服务商与代码适配器

  -------------------------------------------------------------------------------------------------------------------------------------
  服务商/产品       配置协议                                  适配器类                         配置重点
  ----------------- ----------------------------------------- -------------------------------- ----------------------------------------
  OpenAI Responses  `openai_responses`                        `OpenAIResponsesProvider`        OpenAI API Key、账户可用的 Responses
  API；部分 Codex                                                                              模型 ID
  相关工作流/模型                                                                              

  OpenAI Chat       `openai_chat`                             `OpenAICompatibleChatProvider`   OpenAI API Key、可用 Chat 模型 ID
  Completions API                                                                              

  Anthropic Claude  `anthropic_messages`                      `AnthropicMessagesProvider`      Anthropic API Key、可用 Claude 模型 ID
  / Claude Opus                                                                                

  Xiaomi MiMo       `openai_chat`（若所用端点提供兼容格式）   `OpenAICompatibleChatProvider`   MiMo 官方 Base URL、模型 ID、具体 token
                                                                                               参数

  DeepSeek          `openai_chat` 或按官方支持的协议扩展      `OpenAICompatibleChatProvider`   DeepSeek Base URL、模型 ID

  Moonshot AI /     `openai_chat`（兼容端点）                 `OpenAICompatibleChatProvider`   与账号区域相符的 Base URL、模型 ID
  Kimi                                                                                         

  火山引擎方舟 Ark  `openai_chat`（兼容端点）                 `OpenAICompatibleChatProvider`   区域 Base URL、模型名或 Endpoint ID

  其他服务商        视官方 API 协议决定                       复用或新增适配器                 核对认证方式、请求格式、响应格式及参数
  -------------------------------------------------------------------------------------------------------------------------------------

注意： - "Codex"也可能指本地编码智能体/CLI；本项目的 `openai_responses`
适配器只发起 API 请求，不会启动本地 Codex CLI。 -
这些协议名是项目内部的适配器标识，不是服务商品牌名。 -
不能假设所有模型支持相同的 token
字段、推理参数、工具调用或多模态输入。 - 具体模型
ID、区域地址和权限会变化。下方官方链接是核对入口，不代表所有账户均已开通所有模型。

## 第一步：确认你手里的 API 属于哪家

如果 API Key 来自官方服务商，使用其官方 Base URL 和模型 ID。

如果 API Key 来自第三方模型聚合平台： 1. 打开该平台控制台或 API 文档；
2. 找到 API Base URL； 3. 找到该平台要求的模型标识； 4. 确认它兼容
OpenAI Chat Completions、OpenAI Responses 或 Anthropic Messages
中的哪一种协议； 5. 若平台使用自定义协议，不能只修改
`base_url`，需要实现对应适配器。

不要将 API Key 粘贴到聊天中请求助手代填。

## 第二步：安装依赖并复制配置

在项目根目录（包含 `SKILL.md` 与 `model_api/` 的目录）执行：

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r model_api/requirements.txt
Copy-Item model_api/config.example.yaml model_api/config.yaml
Copy-Item model_api/.env.example model_api/.env
```

macOS/Linux 可使用：

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r model_api/requirements.txt
cp model_api/config.example.yaml model_api/config.yaml
cp model_api/.env.example model_api/.env
```

## 第三步：填写本机 API Key

打开 `model_api/.env`，只填写你准备使用的服务商对应的变量，例如：

``` dotenv
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
MIMO_API_KEY=
DEEPSEEK_API_KEY=
KIMI_API_KEY=
ARK_API_KEY=
```

将对应变量的等号后填入你自己的密钥。不要把真实密钥提交到 Git，也不要放进
`config.yaml` 或 Python 文件。项目的 `.gitignore` 已排除 `.env` 和本地
`config.yaml`。

如果你使用第三方聚合平台，建议使用明确的变量名（如
`MY_GATEWAY_API_KEY`），并在配置里的 `api_key_env` 对应修改。

## 第四步：修改 `model_api/config.yaml`

找到你要用的服务商配置块，设置： - `protocol`：该 API 兼容的协议； -
`base_url`：服务商提供的 Base URL； - `api_key_env`：本机 `.env`
里的变量名； - `model`：服务商 API 要求的模型 ID； -
`max_tokens_param`：该端点实际支持的 token 参数名。

示例：MiMo UltraSpeed（以小米官方 API 端点为例）

``` yaml
mimo:
  protocol: openai_chat
  base_url: https://api.xiaomimimo.com/v1
  api_key_env: MIMO_API_KEY
  model: mimo-v2.6-pro-ultraspeed
  max_tokens: 4096
  max_tokens_param: max_completion_tokens
  timeout_seconds: 180
```

示例：Claude Opus（模型 ID 请按账户可用列表填写）

``` yaml
claude_opus:
  protocol: anthropic_messages
  base_url: https://api.anthropic.com
  api_key_env: ANTHROPIC_API_KEY
  model: YOUR_CLAUDE_OPUS_MODEL_ID
  max_tokens: 4096
  timeout_seconds: 180
```

示例：DeepSeek（模型 ID 请以官方文档为准）

``` yaml
deepseek:
  protocol: openai_chat
  base_url: https://api.deepseek.com
  api_key_env: DEEPSEEK_API_KEY
  model: YOUR_DEEPSEEK_MODEL_ID
  max_tokens: 4096
  max_tokens_param: max_tokens
  timeout_seconds: 180
```

示例：火山方舟 Ark

``` yaml
volcengine:
  protocol: openai_chat
  base_url: https://ark.cn-beijing.volces.com/api/v3
  api_key_env: ARK_API_KEY
  model: YOUR_ARK_MODEL_OR_ENDPOINT_ID
  max_tokens: 4096
  max_tokens_param: max_tokens
  timeout_seconds: 180
```

以上是配置结构示例。某些型号或账户可能需要不同参数；不要把占位符
`YOUR_...` 当成真实模型 ID。

## 第五步：决定哪些写作阶段使用哪个模型

在配置文件顶部调整角色映射：

``` yaml
default_provider: mimo

roles:
  research_synthesis: deepseek
  drafting: mimo
  review: claude_opus
```

-   `research_synthesis`：综合已经检索并核验过的资料；
-   `drafting`：撰写一辩稿；
-   `review`：检查逻辑、时长、口播自然度、引用与参考文献对应关系。

这里的 `mimo`、`deepseek`、`claude_opus` 是 `providers:`
下的配置名称。若名称不一致，路由校验会报错。

## 第六步：先做配置检查，再发起真实请求

不联网、不消耗 API 额度的检查：

``` powershell
python -m model_api.cli --config model_api/config.yaml --role drafting --provider mimo --prompt "测试" --dry-run
```

真实 API 请求示例：

``` powershell
python -m model_api.cli --config model_api/config.yaml --role drafting --provider mimo --prompt "请用中文回复：API 接入成功。" --max-tokens 256
```

把 `--provider mimo` 替换成你配置的其他 provider
名称。成功时应看到模型回复；仅 `--dry-run`
成功并不代表密钥或网络已验证。

## 常见错误

-   **401 / Unauthorized**：Key 错误、被截断、过期，或 Key 与 Base URL
    不属于同一服务商。
-   **403 / Forbidden**：账号无权限访问该模型或端点。
-   **404 / model not found**：模型 ID 错误，或将官方模型 ID
    与第三方聚合平台的模型别名混用。
-   **连接失败**：Base URL、区域、代理或网络不正确。
-   **429 / rate limit**：额度不足、速率限制或并发限制。
-   **不支持参数**：`max_tokens` 与 `max_completion_tokens`
    等字段可能不通用；按服务商文档调整
    `max_tokens_param`，必要时新增适配器。
-   **响应为空/格式错误**：目标服务可能有特殊响应结构，需在
    `providers.py` 增加针对该服务的解析逻辑。
-   **模型能聊天但不能自动查网页**：普通文本 API
    不会自动提供联网搜索。必须单独接入网页检索工具，不能让模型凭空生成来源。

## 新增一个目前不支持的服务商

如果新服务商兼容已有协议，通常只需要在 `config.yaml` 新增一个 provider
配置块。

如果不兼容： 1. 在 `model_api/providers.py` 新增适配器类； 2. 实现统一的
`generate(system_prompt, user_prompt, max_tokens)` 方法； 3. 在
`create_provider()` 中注册该协议； 4. 在 `SUPPORTED_PROTOCOLS`
中加入协议名； 5. 添加配置与路由测试； 6. 更新
`model_api/PROVIDER_MATRIX.md`，注明服务商、产品、协议与官方文档。

## 官方文档入口

-   OpenAI Responses
    API：https://platform.openai.com/docs/api-reference/responses
-   OpenAI Chat Completions
    API：https://platform.openai.com/docs/api-reference/chat
-   Anthropic Messages API：https://docs.anthropic.com/en/api/messages
-   DeepSeek API：https://api-docs.deepseek.com/zh-cn/
-   Xiaomi MiMo 文档：https://platform.xiaomimimo.com/docs/zh-CN/
-   Moonshot/Kimi
    文档：https://platform.moonshot.ai/docs/guide/prompt-best-practice
-   火山方舟 OpenAI SDK
    兼容说明：https://docs.volcengine.com/docs/ark/compatible-with-openai-sdk?lang=zh

## 安全与限制

-   不要在聊天、文档、源码仓库中泄露真实 API Key。
-   接口调用可能产生费用；调用前确认账户计费与额度。
-   当前适配器以普通文本请求/响应为主，不等于自动网页搜索、工具调用、文件上传或多模态能力。
-   模型输出的事实、数据和参考文献必须独立核验。
