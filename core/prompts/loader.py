"""
提示词加载器 - 从 YAML 模板加载并渲染提示词
支持环境变量、动态变量、条件分支
"""

import re
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
        cache_key = f"{template_name}_{hash(str(variables))}"
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
        
        # 渲染模板
        rendered = self._render_template(template_content, variables)
        
        # 缓存结果
        self._cache[cache_key] = rendered
        
        # 注册到注册表
        self.registry.register(config)
        
        logger.info(f"已加载模板：{template_name} (v{config.version})")
        return rendered
    
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
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """渲染模板（支持多种变量语法）"""
        result = template
        
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
            return str(variables.get(var_name, match.group(0)))
        result = re.sub(var_pattern, var_replacer, result)
        
        # 3. 条件块处理：{%if CONDITION%}...{%endif%}
        if_pattern = r'\{%if\s+(\w+)\s*%\}(.*?)\{%endif%\}'
        def if_replacer(match):
            condition_var = match.group(1)
            content = match.group(2)
            if variables.get(condition_var) or os.environ.get(condition_var):
                return content
            return ''
        result = re.sub(if_pattern, if_replacer, result, flags=re.DOTALL)
        
        # 4. 循环块处理：{%for ITEM in LIST%}...{%endfor%}
        for_pattern = r'\{%for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%endfor%\}'
        def for_replacer(match):
            item_var = match.group(1)
            list_var = match.group(2)
            content = match.group(3)
            items = variables.get(list_var, [])
            if not items:
                return ''
            
            rendered_items = []
            for item in items:
                item_content = content.replace(f'{{{item_var}}}', str(item))
                rendered_items.append(item_content)
            return '\n'.join(rendered_items)
        result = re.sub(for_pattern, for_replacer, result, flags=re.DOTALL)
        
        return result
    
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
