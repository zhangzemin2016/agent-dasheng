"""
提示词管理模块 - Prompt DSL System
支持条件加载、变量插值、版本管理

架构分层：
1. PromptTemplate (loader.py) - 最底层，负责模板渲染
2. PromptLoader (loader.py) - 中间层，负责从 YAML 加载
3. PromptRegistry (prompt_registry.py) - 最上层，负责注册管理
"""

from .loader import PromptTemplate, PromptLoader, get_prompt_loader, reset_prompt_loader
from .prompt_registry import PromptConfig, PromptRegistry, get_registry, reset_registry

__all__ = [
    # 核心类
    'PromptTemplate',      # 模板渲染（最底层）
    'PromptLoader',        # 文件加载（中间层）
    'PromptRegistry',      # 注册管理（最上层）
    'PromptConfig',        # 配置对象
    
    # 工厂函数
    'get_prompt_loader',
    'reset_prompt_loader',
    'get_registry',
    'reset_registry',
]
