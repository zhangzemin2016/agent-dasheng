"""
提示词加载器 - Prompt Loader
负责从 YAML 文件加载模板并创建 PromptTemplate 对象
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from utils.logger import get_logger
from .prompt_registry import PromptConfig

logger = get_logger("prompts.loader")


class PromptTemplate:
    """
    提示词模板 - 最底层，负责模板渲染
    
    职责：
    - 存储模板内容和变量定义
    - 渲染模板（变量替换、条件块、循环块）
    - 验证变量
    
    不负责：
    - 从文件加载（这是 PromptLoader 的职责）
    - 注册管理（这是 PromptRegistry 的职责）
    """

    def __init__(
        self,
        module: str,
        pattern: str,
        variables: Optional[Dict[str, Any]] = None,
        validators: Optional[List[str]] = None
    ):
        self.module = module
        self.pattern = pattern
        self.variables = variables or {}
        self.validators = validators or []

    def render(self, **kwargs) -> str:
        """
        渲染模板（支持多种变量语法）

        Args:
            **kwargs: 动态变量

        Returns:
            渲染后的字符串
        """
        import re

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


class PromptLoader:
    """
    提示词加载器 - 从 YAML 文件加载模板
    
    职责：
    - 从 YAML 文件读取配置和模板内容
    - 创建 PromptTemplate 对象
    - 检查加载条件
    - 缓存已加载的模板
    
    不负责：
    - 渲染模板（这是 PromptTemplate 的职责）
    - 注册管理（这是 PromptRegistry 的职责）
    """

    def __init__(self, templates_dir: str = ""):
        self.templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"
        self._cache: Dict[str, PromptTemplate] = {}
        self._configs: Dict[str, PromptConfig] = {}

    def load_template(self, template_name: str, **variables) -> Optional[str]:
        """
        加载并渲染模板

        Args:
            template_name: 模板名称（不含扩展名）
            **variables: 动态变量

        Returns:
            渲染后的提示词字符串
        """
        # 检查缓存
        cache_key = f"{template_name}_{hash(str(sorted(variables.items())))}"
        if cache_key in self._cache:
            logger.debug(f"从缓存加载模板：{template_name}")
            template_obj = self._cache[cache_key]
            return template_obj.render(**variables)

        # 查找 YAML 文件
        template_path = self.templates_dir / f"{template_name}.yaml"
        if not template_path.exists():
            # 尝试 .yml 扩展名
            template_path = self.templates_dir / f"{template_name}.yml"

        if not template_path.exists():
            logger.error(f"模板文件不存在：{template_path}")
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"解析 YAML 模板失败：{e}")
            return None

        # 提取配置
        config_data = template_data.get('config', {})
        config = PromptConfig(
            name=config_data.get('name', template_name),
            version=config_data.get('version', '1.0'),
            description=config_data.get('description'),
            conditions=config_data.get('conditions', {}),
            tags=config_data.get('tags', []),
            author=config_data.get('author'),
        )

        # 检查加载条件
        if not self._check_conditions(config.conditions):
            logger.warning(f"模板 {template_name} 不满足加载条件，跳过")
            return None

        # 提取模板内容
        template_content = template_data.get('template', '')

        # 提取变量定义（如果有）
        variables_def = template_data.get('variables', {})

        # 创建 PromptTemplate 对象
        template_obj = PromptTemplate(
            module=template_name,
            pattern=template_content,
            variables=variables_def
        )

        # 缓存模板对象和配置
        self._cache[cache_key] = template_obj
        self._configs[template_name] = config

        logger.info(f"已加载模板：{template_name} (v{config.version})")

        # 渲染并返回
        return template_obj.render(**variables)

    def get_template_object(self, template_name: str) -> Optional[PromptTemplate]:
        """
        获取 PromptTemplate 对象（用于高级用法）

        Args:
            template_name: 模板名称

        Returns:
            PromptTemplate 对象
        """
        # 尝试从缓存获取
        for key, template_obj in self._cache.items():
            if key.startswith(f"{template_name}_"):
                return template_obj

        # 如果没缓存，先加载
        if template_name in self._configs or self._load_config(template_name):
            # 创建一个默认缓存 key
            cache_key = f"{template_name}_0"
            if cache_key not in self._cache:
                # 重新加载以创建模板对象
                self.load_template(template_name)
            return self._cache.get(cache_key)

        return None

    def get_config(self, template_name: str) -> Optional[PromptConfig]:
        """获取配置对象"""
        return self._configs.get(template_name)

    def _load_config(self, template_name: str) -> bool:
        """仅加载配置（不创建模板对象）"""
        template_path = self.templates_dir / f"{template_name}.yaml"
        if not template_path.exists():
            template_path = self.templates_dir / f"{template_name}.yml"

        if not template_path.exists():
            return False

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)

            config_data = template_data.get('config', {})
            config = PromptConfig(
                name=config_data.get('name', template_name),
                version=config_data.get('version', '1.0'),
                description=config_data.get('description'),
                conditions=config_data.get('conditions', {}),
                tags=config_data.get('tags', []),
                author=config_data.get('author'),
            )
            self._configs[template_name] = config
            return True
        except Exception as e:
            logger.error(f"加载配置失败：{e}")
            return False

    def _check_conditions(self, conditions: Dict) -> bool:
        """检查加载条件"""
        if not conditions:
            return True

        # 环境变量条件
        env_conditions = conditions.get('env', {})
        for key, expected_value in env_conditions.items():
            actual_value = os.environ.get(key, '')
            if actual_value != expected_value:
                return False

        # 特性开关条件
        feature_conditions = conditions.get('features', [])
        for feature in feature_conditions:
            if not os.environ.get(f"FEATURE_{feature.upper()}", '0') == '1':
                return False

        return True

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("提示词缓存已清空")

    def reload_all(self, **variables):
        """重新加载所有模板"""
        self.clear_cache()

        for template_file in self.templates_dir.glob("*.yaml"):
            template_name = template_file.stem
            self.load_template(template_name, **variables)

        logger.info(f"已重新加载 {len(self._cache)} 个模板")

    def list_templates(self) -> List[str]:
        """列出所有已加载的模板"""
        return list(self._configs.keys())


# 全局加载器实例
_loader: Optional[PromptLoader] = None


def get_prompt_loader(templates_dir: str = "") -> PromptLoader:
    """获取全局 PromptLoader 实例"""
    global _loader
    if _loader is None:
        _loader = PromptLoader(templates_dir)
    return _loader


def reset_prompt_loader():
    """重置全局加载器（主要用于测试）"""
    global _loader
    _loader = None
