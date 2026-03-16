"""
提示词加载器 - 从 YAML 模板加载并渲染提示词
支持环境变量、动态变量、条件分支
使用 PromptTemplate 对象进行渲染
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

from utils.logger import get_logger
from .prompt_registry import PromptConfig, PromptTemplate, PromptRegistry

logger = get_logger("prompts.loader")


class PromptLoader:
    """提示词加载器"""

    def __init__(self, templates_dir: str = ""):
        self.templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"
        self.registry = PromptRegistry()
        self._cache: Dict[str, str] = {}

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
            return self._cache[cache_key]

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

        # 创建 PromptTemplate 对象并使用其 render 方法
        template_obj = PromptTemplate(
            module=template_name,
            pattern=template_content,
            variables=variables_def
        )

        # 渲染模板（使用 PromptTemplate.render 方法）
        rendered = template_obj.render(**variables)

        # 缓存结果
        self._cache[cache_key] = rendered

        # 注册到注册表（同时注册配置和模板对象）
        self.registry.register(config, template_obj)

        logger.info(f"已加载模板：{template_name} (v{config.version})")
        return rendered

    def get_template_object(self, template_name: str) -> Optional[PromptTemplate]:
        """
        获取 PromptTemplate 对象（用于高级用法）

        Args:
            template_name: 模板名称

        Returns:
            PromptTemplate 对象
        """
        return self.registry.get_template(template_name)

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
        return self.registry.list_templates()


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
