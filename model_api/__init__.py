"""Multi-provider LLM adapter layer for the debatingskills project (debatingspeech skill)."""
from .providers import ModelResult, ModelRouter, ProviderError, create_provider, load_config

__all__ = ["ModelResult", "ModelRouter", "ProviderError", "create_provider", "load_config"]
