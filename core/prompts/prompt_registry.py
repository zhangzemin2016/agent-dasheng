"""
提示词注册表 - Prompt Registry (DSL 核心)
支持条件加载、变量插值、版本管理
"""

import re
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any


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
    variables: Dict[str, Any] = field(default_factory=dict)   # 可用变量定义及默认值
    validators: List[str] = field(default_factory=list)  # 验证规则

    def render(self, **kwargs) -> str:
        """
        渲染模板（支持多种变量语法）

        Args:
            **kwargs: 动态变量

        Returns:
            渲染后的字符串
        """
        result = self.pattern

        # 合并默认变量和动态变量
        all_vars = {**self.variables, **kwargs}

        # 1. 环境变量替换：${ENV_VAR} 或 {%ENV_VAR%}
        env_pattern = r'\$\{(\w+)\}|\{%(\w+)%\}'

        def env_replacer(match):
            env_var = match.group(1) or match.group(2)
            return os.environ.get(env_var, match.group(0))

        result = re.sub(env_pattern, env_replacer, result)

        # 2. 动态变量替换：{{variable}} 或 {variable}
        var_pattern = r'\{\{(\w+)\}\}|\{(\w+)\}'

        def var_replacer(match):
            var_name = match.group(1) or match.group(2)
            return str(all_vars.get(var_name, match.group(0)))

        result = re.sub(var_pattern, var_replacer, result)

        # 3. 条件块处理：{%if CONDITION%}...{%endif%}
        if_pattern = r'\{%if\s+(\w+)\s*%\}(.*?)\{%endif%\}'

        def if_replacer(match):
            condition_var = match.group(1)
            content = match.group(2)
            if all_vars.get(condition_var) or os.environ.get(condition_var):
                return content
            return ''

        result = re.sub(if_pattern, if_replacer, result, flags=re.DOTALL)

        # 4. 循环块处理：{%for ITEM in LIST%}...{%endfor%}
        for_pattern = r'\{%for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%endfor%\}'

        def for_replacer(match):
            item_var = match.group(1)
            list_var = match.group(2)
            content = match.group(3)
            items = all_vars.get(list_var, [])
            if not items:
                return ''

            rendered_items = []
            for item in items:
                item_content = content.replace(f'{{{item_var}}}', str(item))
                rendered_items.append(item_content)
            return '\n'.join(rendered_items)

        result = re.sub(for_pattern, for_replacer, result, flags=re.DOTALL)

        return result

    def validate(self, **kwargs) -> List[str]:
        """
        验证变量

        Args:
            **kwargs: 待验证的变量

        Returns:
            错误消息列表（空列表表示验证通过）
        """
        errors = []

        # 检查必填变量
        for var_name, var_value in self.variables.items():
            if var_value is ...:  # Ellipsis 表示必填
                if var_name not in kwargs:
                    errors.append(f"Missing required variable: {var_name}")

        # 应用自定义验证规则
        for validator in self.validators:
            if validator == 'no_empty_strings':
                for key, value in kwargs.items():
                    if isinstance(value, str) and not value.strip():
                        errors.append(f"Variable '{key}' cannot be empty")

        return errors


class PromptRegistry:
    """提示词注册表 - 集中管理所有提示词"""

    def __init__(self):
        self._modules: Dict[str, PromptConfig] = {}
        self._templates: Dict[str, PromptTemplate] = {}
        self._loaders: Dict[str, Callable] = {}

    def register(self, config: PromptConfig, template: Optional[PromptTemplate] = None):
        """
        注册提示词模块和模板

        Args:
            config: 配置对象
            template: 可选的模板对象（如果为 None，只注册配置）
        """
        self._modules[config.name] = config
        if template:
            self._templates[config.name] = template

    def register_template(self, name: str, pattern: str, **kwargs):
        """
        快速注册模板

        Args:
            name: 模板名称
            pattern: 模板字符串
            **kwargs: 变量定义和默认值
        """
        template = PromptTemplate(module=name, pattern=pattern, variables=kwargs)
        self._templates[name] = template

    def get_config(self, name: str) -> Optional[PromptConfig]:
        """获取配置（支持条件过滤）"""
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

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """获取模板对象"""
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

        # 渲染模板
        return template.render(**kwargs)

    def list_templates(self) -> List[str]:
        """列出所有已注册的模板"""
        return list(self._templates.keys())

    def save(self, module_name: str, version: Optional[str] = None):
        """保存到文件（支持版本控制）"""
        pass


# 初始化全局注册表
registry = PromptRegistry()
