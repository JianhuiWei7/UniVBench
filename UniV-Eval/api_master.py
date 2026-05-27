import os

from openai import AsyncOpenAI, AsyncAzureOpenAI
from agents import (
    Model,
    ModelProvider,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    set_tracing_disabled,
)
from agents.extensions.models.litellm_model import LitellmModel


TEMPERATURE = 0.0001
MAX_TOKEN = 32768

set_tracing_disabled(disabled=True)


# ByteDance Seed model setup
SEED_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
SEED_API_KEY = os.getenv("SEED_API_KEY")
if not SEED_API_KEY:
    raise ValueError("ARK_API_KEY environment variable not set. Please set it before running.")

SEED_MODEL_NAME = "doubao-seed-2-0-pro-260215"
ark_client = AsyncOpenAI(base_url=SEED_BASE_URL, api_key=SEED_API_KEY)


class ArkProvider(ModelProvider):
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    def get_model(self, model_name: str | None) -> Model:
        self.used_model_name = model_name or self.model_name or SEED_MODEL_NAME
        return OpenAIChatCompletionsModel(
            model=self.used_model_name,
            openai_client=ark_client,
        )


SEED_RUN_CONFIG = RunConfig(
    model_provider=ArkProvider(model_name=SEED_MODEL_NAME),
    model_settings=ModelSettings(
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKEN,
    ),
)

def get_seed_run_config(model_name, temperature, max_tokens):
    return RunConfig(
        model_provider=ArkProvider(model_name=model_name),
        model_settings=ModelSettings(
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )


# Azure OpenAI setup
OPENAI_MODEL_NAME = "gpt-5.5"
AZURE_OPENAI_BASE_URL = "https://search-va.byteintl.net/gpt/openapi/online/v2/crawl"
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_client = AsyncAzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-03-01-preview",
    azure_endpoint=AZURE_OPENAI_BASE_URL,
)


class AzureOpenAIProvider(ModelProvider):
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    def get_model(self, model_name: str | None) -> Model:
        used_model_name = model_name or self.model_name or OPENAI_MODEL_NAME
        return OpenAIChatCompletionsModel(
            model=used_model_name,
            openai_client=azure_openai_client,
        )


AZURE_OPENAI_RUN_CONFIG = RunConfig(
    model_provider=AzureOpenAIProvider(),
    model_settings=ModelSettings(
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKEN,
    ),
)


# OpenAI-compatible internal endpoint setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://genai-va-og.tiktok-row.org/gpt/openapi/online/v2/crawl/openai/deployments/gpt_openapi"
openai_agent = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    default_headers={"Api-Key": OPENAI_API_KEY},
)


class OpenAIProvider(ModelProvider):
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    def get_model(self, model_name: str | None) -> Model:
        used_model_name = model_name or self.model_name or OPENAI_MODEL_NAME
        return OpenAIChatCompletionsModel(
            model=used_model_name,
            openai_client=openai_agent,
        )


OPENAI_RUN_CONFIG = RunConfig(
    model_provider=OpenAIProvider(),
    model_settings=ModelSettings(
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKEN,
    ),
)


# Gemini setup
GEMINI_BASE_URL = "https://genai-va-og.tiktok-row.org/gpt/openapi/online/multimodal/crawl"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "azure/gemini-2.5-pro-preview-05-06"
gemini_model = LitellmModel(
    model=GEMINI_MODEL_NAME,
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)

GEMINI_RUN_CONFIG = RunConfig(
    model=gemini_model,
    model_settings=ModelSettings(
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKEN,
    ),
)
