"""
LangChain LLM 工厂
支持多提供商：OpenAI、DeepSeek、Ollama 等
"""

from typing import Dict, Any, Optional
from pathlib import Path

from utils.logger import get_logger
from core.config_manager import get_config_manager

logger = get_logger("llm.langchain_factory")


def get_llm(temperature: float = 0.7, **kwargs):
    """
    获取 LangChain LLM 实例
    
    Args:
        temperature: 温度参数 (0-1)
        **kwargs: 其他参数
        
    Returns:
        LangChain ChatModel 实例
    """
    config = get_config_manager()
    llm_config = config.get_llm_settings()
    
    provider = llm_config.get("provider", "ollama")
    provider_config = llm_config.get("providers", {}).get(provider, {})
    
    model = provider_config.get("model", "")
    
    logger.info(f"使用 LangChain LLM: {provider} / {model}")
    
    # 根据提供商创建对应的 ChatModel
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        
        api_key = provider_config.get("api_key", "")
        base_url = provider_config.get("base_url", "")
        
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url if base_url else None,
            temperature=temperature,
            streaming=True,
            **kwargs
        )
        
    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        
        api_key = provider_config.get("api_key", "")
        
        # DeepSeek 使用 OpenAI 兼容接口
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://api.deepseek.com",
            temperature=temperature,
            streaming=True,
            **kwargs
        )
        
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        
        base_url = provider_config.get("base_url", "http://localhost:11434")
        
        llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )
        
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        
        api_key = provider_config.get("api_key", "")
        
        llm = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature,
            streaming=True,
            **kwargs
        )
        
    else:
        # 默认使用 Ollama
        from langchain_ollama import ChatOllama
        
        llm = ChatOllama(
            model=model or "llama2",
            temperature=temperature,
            **kwargs
        )
        logger.warning(f"未知提供商 {provider}，使用 Ollama 默认配置")
    
    logger.info(f"LangChain LLM 初始化成功：{type(llm).__name__}")
    return llm


def get_llm_sync(temperature: float = 0.7, **kwargs):
    """
    获取同步 LLM 实例（用于不支持异步的场景）
    
    Args:
        temperature: 温度参数 (0-1)
        **kwargs: 其他参数
        
    Returns:
        LangChain ChatModel 实例
    """
    return get_llm(temperature=temperature, **kwargs)
