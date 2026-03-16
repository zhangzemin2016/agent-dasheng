"""
提示词注册表 - Prompt Registry
负责注册和管理已加载的模板，提供统一的访问入口

不依赖 PromptLoader 或 PromptTemplate，避免循环导入
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
import os

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from .loader import PromptTemplate


@dataclass
class PromptConfig:
    """提示词配置（YAML/JSON Schema）"""
    name: str                          # 模块名称
    version: str = "1.0"               # 版本控制
    description: Optional[str] = None  # 描述
    conditions: Dict = field(default_factory=dict)  # 加载条件
    base_path: str = ""                # 文件路径
    author: Optional[str] = None
    created_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class PromptRegistry:
    """
    提示词注册表 - 集中管理所有已加载的模板
    
    职责：
    - 注册和管理 PromptTemplate 对象
    - 提供统一的访问接口
    - 支持条件过滤和标签筛选
    
    不负责：
    - 从文件加载模板（这是 PromptLoader 的职责）
    - 渲染模板（这是 PromptTemplate 的职责）
    """

    def __init__(self):
        self._modules: Dict[str, PromptConfig] = {}
        self._templates: Dict[str, "PromptTemplate"] = {}

    def register(self, config: PromptConfig, template: Optional["PromptTemplate"] = None):
        """
        注册提示词模块和模板
        
        Args:
            config: 配置对象
            template: 模板对象（可选）
        """
        self._modules[config.name] = config
        if template:
            self._templates[config.name] = template

    def get_config(self, name: str) -> Optional[PromptConfig]:
        """
        获取配置（支持条件过滤）
        
        Args:
            name: 模块名称
            
        Returns:
            PromptConfig 对象，如果不满足条件则返回 None
        """
        if name not in self._modules:
            return None

        config = self._modules[name]

        # 应用条件过滤
        conditions = config.conditions.get('conditions', {})
        env_conditions = conditions.get('env', {})

        for key, expected_value in env_conditions.items():
            actual_value = os.environ.get(key, '')
            if actual_value != expected_value:
                return None

        return config

    def get_template(self, name: str) -> Optional["PromptTemplate"]:
        """
        获取模板对象
        
        Args:
            name: 模板名称
            
        Returns:
            PromptTemplate 对象
        """
        return self._templates.get(name)

    def load(self, module_name: str, **kwargs) -> Optional[str]:
        """
        加载并渲染提示词
        
        Args:
            module_name: 模块名称
            **kwargs: 动态变量
            
        Returns:
            渲染后的字符串
        """
        config = self.get_config(module_name)
        if not config:
            return None

        # 检查 tags 过滤
        filter_tags = kwargs.get('_tags', [])
        if filter_tags and set(filter_tags).isdisjoint(set(config.tags)):
            return None

        template = self._templates.get(module_name)
        if not template:
            raise ValueError(f"No template for module: {module_name}")

        # 验证变量
        errors = template.validate(**kwargs)
        if errors:
            raise ValueError(f"Template validation failed: {', '.join(errors)}")

        # 渲染模板（委托给 PromptTemplate.render）
        return template.render(**kwargs)

    def list_templates(self) -> List[str]:
        """列出所有已注册的模板"""
        return list(self._templates.keys())

    def clear(self):
        """清空所有注册"""
        self._modules.clear()
        self._templates.clear()


# 全局注册表实例
_registry: Optional[PromptRegistry] = None


def get_registry() -> PromptRegistry:
    """获取全局 PromptRegistry 实例"""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def reset_registry():
    """重置全局注册表（主要用于测试）"""
    global _registry
    _registry = None
