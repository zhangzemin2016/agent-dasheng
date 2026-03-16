"""
提示词注册表 - Prompt Registry (DSL 核心)
支持条件加载、变量插值、版本管理
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable
import json


@dataclass
class PromptConfig:
    """提示词配置（YAML/JSON Schema）"""
    name: str                          # 模块名称（如 role, capabilities）
    version: str = "1.0"               # 版本控制
    description: Optional[str] = None  # 描述
    
    # 加载条件（动态管理）
    conditions: Dict = field(default_factory=dict)
    
    # 文件路径（支持多级目录）
    base_path: str = ""
    
    # 元数据
    author: Optional[str] = None
    created_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass  
class PromptTemplate:
    """提示词模板（支持变量插值）"""
    module: str                        # 所属模块名
    pattern: str                       # Jinja2/Python f-string 模板
    variables: Dict = field(default_factory=dict)   # 可用变量定义
    validators: List[str] = field(default_factory=list)  # 验证规则


class PromptRegistry:
    """提示词注册表 - 集中管理所有提示词"""
    
    def __init__(self):
        self._modules: Dict[str, PromptConfig] = {}
        self._templates: Dict[str, PromptTemplate] = {}
        self._loaders: Dict[str, Callable] = {}
        
    def register(self, config: PromptConfig):
        """注册提示词模块"""
        self._modules[config.name] = config
        
    def get_config(self, name: str) -> Optional[PromptConfig]:
        """获取配置（支持条件过滤）"""
        if name not in self._modules:
            return None
        
        config = self._modules[name]
        
        # 应用条件过滤
        conditions = config.conditions.get('conditions', {})
        env_conditions = conditions.get('env', [])
        
        import os
        current_env = os.environ.get('ENV', 'dev')
        
        if env_conditions:
            required = set(env_conditions)
            available = set(os.environ.keys())
            if not required.issubset(available):
                return None
        
        return config
    
    def load(self, module_name: str, **kwargs) -> Optional[str]:
        """加载提示词（支持环境变量插值）"""
        config = self.get_config(module_name)
        if not config:
            return None
        
        # 检查 tags 过滤
        filter_tags = kwargs.get('tags', [])
        if filter_tags and set(filter_tags).isdisjoint(set(config.tags)):
            return None
        
        template = self._templates.get(module_name)
        if not template:
            raise ValueError(f"No template for module: {module_name}")
        
        # 应用变量替换（支持 .format(), f-string, Jinja2）
        content = template.pattern
        
        # 环境变量替换
        import os
        for key, value in os.environ.items():
            pattern = r'\$\{' + re.escape(key) + r'\}|\{%\s*' + re.escape(key) + r'\s*%\}'
            content = re.sub(pattern, lambda m: value if len(m.group()) > 0 else content, content)
        
        return content
    
    def save(self, module_name: str, version: Optional[str] = None):
        """保存到文件（支持版本控制）"""
        pass


# 初始化全局注册表
registry = PromptRegistry()
