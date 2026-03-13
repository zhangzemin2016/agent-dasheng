from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from core.config_manager import get_config_manager
from utils.logger import get_logger

logger = get_logger("llm_factory")

# 获取全局配置管理器实例
_config = get_config_manager()


def get_llm(temperature: float):
    """
    获取 LLM 实例

    Args:
        temperature: 温度参数，控制生成随机性

    Returns:
        LLM 实例

    Raises:
        ValueError: 不支持的 LLM 提供商
    """
    # 从配置管理器获取当前 provider
    llm_settings = _config.get_llm_settings()
    provider = llm_settings["provider"]

    logger.info(f"使用 LLM 提供商：{provider}")

    config = _config.get_llm_config(provider)

    if provider == "deepseek":
        model = config.get("model")
        logger.debug(f"DeepSeek 模型: {model}")
        return ChatDeepSeek(
            model=model,
            temperature=temperature,
            api_key=config.get("api_key")
        )
    elif provider == "ollama":
        model = config.get("model")
        logger.debug(f"Ollama 模型: {model}")
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=config.get("base_url")
        )
    elif provider == "openai":
        model = config.get("model")
        logger.debug(f"OpenAI 模型: {model}")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=config.get("api_key")
        )
    else:
        raise ValueError(f"不支持的 LLM_PROVIDER: {LLM_PROVIDER}")
