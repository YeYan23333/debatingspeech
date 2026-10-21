import unittest

from model_api.providers import (
    ProviderError,
    resolve_provider_name,
    validate_config,
)


SAMPLE = {
    "default_provider": "deepseek",
    "roles": {"drafting": "claude_opus", "review": "mimo"},
    "providers": {
        "deepseek": {
            "protocol": "openai_chat",
            "api_key_env": "DEEPSEEK_API_KEY",
            "model": "deepseek-flash",
        },
        "claude_opus": {
            "protocol": "anthropic_messages",
            "api_key_env": "ANTHROPIC_API_KEY",
            "model": "YOUR_CLAUDE_OPUS_MODEL_ID",
        },
        "mimo": {
            "protocol": "openai_chat",
            "api_key_env": "MIMO_API_KEY",
            "model": "YOUR_MIMO_MODEL_ID",
        },
        "codex": {
            "protocol": "openai_responses",
            "api_key_env": "OPENAI_API_KEY",
            "model": "YOUR_CODEX_MODEL_ID",
        },
    },
}


class ProviderConfigTests(unittest.TestCase):
    def test_config_validates_without_network(self):
        validate_config(SAMPLE)

    def test_role_route(self):
        self.assertEqual(resolve_provider_name(SAMPLE, role="drafting"), "claude_opus")

    def test_override_has_priority(self):
        self.assertEqual(
            resolve_provider_name(SAMPLE, role="drafting", provider_override="codex"),
            "codex",
        )

    def test_default_route(self):
        self.assertEqual(resolve_provider_name(SAMPLE), "deepseek")

    def test_unknown_role_provider_fails(self):
        config = {
            **SAMPLE,
            "roles": {"drafting": "not_configured"},
        }
        with self.assertRaises(ProviderError):
            validate_config(config)

    def test_unknown_protocol_fails(self):
        config = {
            "default_provider": "bad",
            "providers": {
                "bad": {
                    "protocol": "magic_api",
                    "api_key_env": "SOME_KEY",
                    "model": "some-model",
                }
            },
        }
        with self.assertRaises(ProviderError):
            validate_config(config)


if __name__ == "__main__":
    unittest.main()
