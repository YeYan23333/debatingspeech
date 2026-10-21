"""CLI smoke-test and call entry point for the multi-provider model adapter."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .providers import ModelRouter, ProviderError, load_config, resolve_provider_name


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 debatingskills 项目中 debatingspeech Skill 配置的模型 API")
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.example.yaml")))
    parser.add_argument("--role", default="drafting", help="配置中的任务角色，如 drafting/review/research_synthesis")
    parser.add_argument("--provider", help="临时指定 provider，优先级高于 role 路由")
    parser.add_argument("--system", default="你是一名严谨的华语辩论研究与写作助手。")
    parser.add_argument("--prompt", required=True, help="要发送给模型的提示词")
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="仅检查路由配置，不调用 API")
    args = parser.parse_args()

    try:
        try:
            from dotenv import load_dotenv
            # Load the .env file beside this CLI module (model_api/.env), independent
            # of the current working directory. Existing OS environment variables win.
            env_path = Path(__file__).with_name(".env")
            load_dotenv(dotenv_path=env_path, override=False)
        except ImportError:
            # Users can still set MIMO_API_KEY (and other keys) in the shell environment.
            pass

        config = load_config(args.config)
        provider_name = resolve_provider_name(
            config, role=args.role, provider_override=args.provider
        )
        provider_cfg = config["providers"][provider_name]

        if args.dry_run:
            print("Dry run：配置解析成功，未调用网络 API。")
            print(f"角色: {args.role}")
            print(f"Provider: {provider_name}")
            print(f"协议: {provider_cfg['protocol']}")
            print(f"Base URL: {provider_cfg.get('base_url', '(SDK 默认)')}")
            print(f"Model: {provider_cfg['model']}")
            print(f"API Key 环境变量名: {provider_cfg['api_key_env']}（不会显示密钥）")
            return 0

        router = ModelRouter(config)
        result = router.generate(
            role=args.role,
            provider_override=args.provider,
            system_prompt=args.system,
            user_prompt=args.prompt,
            max_tokens=args.max_tokens,
        )
        print(result.text)
        print(
            f"\n[provider={result.provider}; model={result.model}; "
            f"response_id={result.response_id or 'n/a'}]",
            file=sys.stderr,
        )
        return 0
    except ProviderError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
