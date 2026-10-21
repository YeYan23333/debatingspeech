"""Provider adapters for OpenAI Responses, OpenAI-compatible chat, and Anthropic Messages.

API keys are read from environment variables named in the YAML config. Never place secrets
inside the config file or commit a real .env file.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
import os


class ProviderError(RuntimeError):
    """Safe, user-facing provider/configuration error."""


@dataclass(frozen=True)
class ModelResult:
    text: str
    provider: str
    model: str
    response_id: str | None = None


class ModelProvider(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> ModelResult:
        ...


# Protocol registry: these are wire/API protocols, not vendor names.
# - openai_chat: OpenAI Chat Completions API; also usable with vendors that document
#   compatibility with this request/response shape (e.g. configured DeepSeek, MiMo,
#   Moonshot/Kimi, and Volcano Engine Ark endpoints).
# - openai_responses: OpenAI Responses API. This is the OpenAI API adapter used for
#   supported Responses-capable models; it does NOT launch the local Codex CLI.
# - anthropic_messages: Anthropic Messages API, intended for Claude / Claude Opus.
SUPPORTED_PROTOCOLS = {
    "openai_chat",
    "openai_responses",
    "anthropic_messages",
}


def load_config(path: str | Path) -> dict[str, Any]:
    """Load YAML configuration. Requires PyYAML."""
    try:
        import yaml
    except ImportError as exc:
        raise ProviderError("缺少 PyYAML 依赖，请先执行：pip install -r model_api/requirements.txt") from exc

    config_path = Path(path)
    if not config_path.exists():
        raise ProviderError(
            f"找不到配置文件：{config_path}。请复制 model_api/config.example.yaml "
            "为 model_api/config.yaml 后再修改。"
        )
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ProviderError(f"配置文件无法解析：{config_path}") from exc
    validate_config(data)
    return data


def validate_config(config: dict[str, Any]) -> None:
    """Validate structure without requiring API keys or making network requests."""
    providers = config.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise ProviderError("配置必须包含非空的 providers 字典。")

    for name, item in providers.items():
        if not isinstance(item, dict):
            raise ProviderError(f"providers.{name} 必须是一个对象。")
        protocol = item.get("protocol")
        if protocol not in SUPPORTED_PROTOCOLS:
            raise ProviderError(
                f"providers.{name}.protocol={protocol!r} 不受支持；"
                f"可选值：{', '.join(sorted(SUPPORTED_PROTOCOLS))}"
            )
        if not item.get("model"):
            raise ProviderError(f"providers.{name}.model 不能为空。")
        if not item.get("api_key_env"):
            raise ProviderError(f"providers.{name}.api_key_env 必须指向环境变量名。")

    roles = config.get("roles", {})
    if roles and not isinstance(roles, dict):
        raise ProviderError("roles 必须是一个对象。")
    known = set(providers)
    for role, provider_name in roles.items():
        if provider_name not in known:
            raise ProviderError(
                f"roles.{role} 指向不存在的 provider：{provider_name!r}。"
            )
    default_provider = config.get("default_provider")
    if default_provider and default_provider not in known:
        raise ProviderError(
            f"default_provider 指向不存在的 provider：{default_provider!r}。"
        )


def resolve_provider_name(
    config: dict[str, Any],
    *,
    role: str | None = None,
    provider_override: str | None = None,
) -> str:
    """Resolve explicit override > role mapping > default provider."""
    providers = config["providers"]
    roles = config.get("roles", {})
    name = provider_override or (roles.get(role) if role else None) or config.get("default_provider")
    if not name:
        raise ProviderError("请在配置中设置 default_provider，或使用 --provider 指定服务商。")
    if name not in providers:
        raise ProviderError(f"未配置名为 {name!r} 的 provider。")
    return name


def _get_api_key(provider_name: str, config: dict[str, Any]) -> str:
    env_name = config["api_key_env"]
    value = os.getenv(env_name, "").strip()
    if not value:
        raise ProviderError(
            f"服务商 {provider_name!r} 需要环境变量 {env_name}。"
            "请在系统环境变量中设置，或在本地 .env 文件中配置；不要把密钥写入 YAML。"
        )
    return value


def create_provider(provider_name: str, config: dict[str, Any]) -> ModelProvider:
    """Create one adapter from a single provider's config."""
    api_key = _get_api_key(provider_name, config)
    protocol = config["protocol"]
    if protocol == "openai_chat":
        return OpenAICompatibleChatProvider(provider_name, config, api_key)
    if protocol == "openai_responses":
        return OpenAIResponsesProvider(provider_name, config, api_key)
    if protocol == "anthropic_messages":
        return AnthropicMessagesProvider(provider_name, config, api_key)
    raise ProviderError(f"不支持的 API 协议：{protocol}")


class OpenAICompatibleChatProvider:
    """OpenAI Chat Completions wire format.

    Vendor mapping depends on the configured base_url/model:
    - OpenAI: https://api.openai.com/v1
    - DeepSeek: https://api.deepseek.com
    - Xiaomi MiMo: use the current official MiMo endpoint for your account
    - Moonshot AI / Kimi: use the regional Moonshot endpoint for your account
    - Volcano Engine Ark: use the Ark endpoint for your region/account
    This class is a compatibility adapter; it does not mean these vendors share one API
    product or support identical optional parameters.
    """

    def __init__(self, name: str, config: dict[str, Any], api_key: str):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("缺少 openai SDK，请执行：pip install -r model_api/requirements.txt") from exc

        self.name = name
        self.config = config
        self.model = config["model"]
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.get("base_url") or None,
            timeout=float(config.get("timeout_seconds", 120)),
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> ModelResult:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt or "你是一名严谨的华语辩论研究与写作助手。"},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }
        token_count = max_tokens or self.config.get("max_tokens", 2048)
        token_param = self.config.get("max_tokens_param", "max_tokens")
        if token_param not in {"max_tokens", "max_completion_tokens"}:
            raise ProviderError(
                f"{self.name}: max_tokens_param 只支持 max_tokens 或 max_completion_tokens。"
            )
        kwargs[token_param] = int(token_count)

        extra_body = self.config.get("extra_body")
        if extra_body:
            kwargs["extra_body"] = extra_body

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            # Avoid echoing request headers or API keys in errors.
            raise ProviderError(
                f"{self.name} 调用失败（{type(exc).__name__}）。请检查 API Key、模型 ID、"
                "Base URL、账户权限、额度和服务商参数。"
            ) from exc

        content = response.choices[0].message.content if response.choices else ""
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
                elif getattr(item, "text", None):
                    parts.append(str(item.text))
            content = "\n".join(parts)
        if not content:
            raise ProviderError(f"{self.name} 返回了空文本；请检查模型输出限制或服务商响应格式。")
        return ModelResult(
            text=str(content),
            provider=self.name,
            model=getattr(response, "model", None) or self.model,
            response_id=getattr(response, "id", None),
        )


class OpenAIResponsesProvider:
    """OpenAI Responses API adapter.

    Vendor/product mapping: OpenAI API (Responses endpoint). Use a model ID available
    to your OpenAI API account. “Codex” may refer to an OpenAI coding product/model family;
    this adapter makes an API request and does not launch or control the local Codex CLI.
    Do not assume third-party OpenAI-compatible Chat Completions endpoints also support
    the Responses API unless that provider explicitly documents it.
    """

    def __init__(self, name: str, config: dict[str, Any], api_key: str):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("缺少 openai SDK，请执行：pip install -r model_api/requirements.txt") from exc

        self.name = name
        self.config = config
        self.model = config["model"]
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.get("base_url") or None,
            timeout=float(config.get("timeout_seconds", 120)),
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> ModelResult:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": user_prompt,
        }
        if system_prompt:
            kwargs["instructions"] = system_prompt
        kwargs["max_output_tokens"] = int(max_tokens or self.config.get("max_tokens", 2048))
        extra_body = self.config.get("extra_body")
        if extra_body:
            kwargs.update(extra_body)

        try:
            response = self.client.responses.create(**kwargs)
        except Exception as exc:
            raise ProviderError(
                f"{self.name} Responses API 调用失败（{type(exc).__name__}）。请检查模型是否支持 "
                "Responses API，以及 Base URL、API Key、账户权限和请求参数。"
            ) from exc

        text = getattr(response, "output_text", "") or ""
        if not text:
            raise ProviderError(f"{self.name} 返回了空文本；请检查模型输出限制或响应格式。")
        return ModelResult(
            text=text,
            provider=self.name,
            model=getattr(response, "model", None) or self.model,
            response_id=getattr(response, "id", None),
        )


class AnthropicMessagesProvider:
    """Anthropic Messages API adapter — Anthropic, Claude / Claude Opus.

    Use an Anthropic API key and a Claude model ID enabled for that account. This is the
    native Anthropic Messages protocol, not the OpenAI Chat Completions protocol.
    """

    def __init__(self, name: str, config: dict[str, Any], api_key: str):
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ProviderError("缺少 anthropic SDK，请执行：pip install -r model_api/requirements.txt") from exc

        self.name = name
        self.config = config
        self.model = config["model"]
        init_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": float(config.get("timeout_seconds", 120)),
        }
        if config.get("base_url"):
            init_kwargs["base_url"] = config["base_url"]
        self.client = Anthropic(**init_kwargs)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> ModelResult:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": int(max_tokens or self.config.get("max_tokens", 2048)),
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if self.config.get("extra_body"):
            # Native Anthropic API has a different parameter contract; add only after
            # verifying the target model/API supports the configured fields.
            kwargs.update(self.config["extra_body"])

        try:
            response = self.client.messages.create(**kwargs)
        except Exception as exc:
            raise ProviderError(
                f"{self.name} Messages API 调用失败（{type(exc).__name__}）。"
                "请检查模型 ID、API Key、账户权限和 Anthropic 原生请求参数。"
            ) from exc

        text_parts = [
            block.text for block in getattr(response, "content", [])
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        text = "\n".join(text_parts).strip()
        if not text:
            raise ProviderError(f"{self.name} 返回了空文本；请检查模型输出限制或响应格式。")
        return ModelResult(
            text=text,
            provider=self.name,
            model=getattr(response, "model", None) or self.model,
            response_id=getattr(response, "id", None),
        )


class ModelRouter:
    """Route different work stages to different providers via config.roles."""

    def __init__(self, config: dict[str, Any]):
        validate_config(config)
        self.config = config
        self._cache: dict[str, ModelProvider] = {}

    def generate(
        self,
        *,
        role: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
        provider_override: str | None = None,
    ) -> ModelResult:
        name = resolve_provider_name(
            self.config, role=role, provider_override=provider_override
        )
        if name not in self._cache:
            self._cache[name] = create_provider(name, self.config["providers"][name])
        return self._cache[name].generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )
