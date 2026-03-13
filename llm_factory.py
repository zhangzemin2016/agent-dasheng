from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from core.config_manager import get_config_manager
from utils.logger import get_logger

logger = get_logger("llm_factory")

# 全局配置管理器实例
_config = get_config_manager()


def get_llm(temperature: float):
    """
    获取 LLM 实例。

    会根据当前配置的 provider（deepseek / ollama / openai 等）
    构造对应的 LangChain Chat 模型实例。
    """
    llm_settings = _config.get_llm_settings()
    provider = llm_settings.get("provider")

    if not provider:
        raise ValueError("LLM 提供商未配置，请先在模型配置中选择 provider")

    logger.info(f"使用 LLM 提供商：{provider}")

    config = _config.get_llm_config(provider)
    model = config.get("model")

    if not model:
        raise ValueError(f"LLM 提供商 {provider} 未配置模型名称")

    if provider == "deepseek":
        logger.debug(f"DeepSeek 模型: {model}")
        return ChatDeepSeek(
            model=model,
            temperature=temperature,
            api_key=config.get("api_key"),
        )

    if provider == "ollama":
        logger.debug(f"Ollama 模型: {model}")
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=config.get("base_url"),
        )

    if provider == "openai":
        logger.debug(f"OpenAI 模型: {model}")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=config.get("api_key"),
        )

    # 未知 provider，给出明确错误
    raise ValueError(f"不支持的 LLM 提供商: {provider}")
