"""
提示词管理器 - 统一入口
整合 PromptLoader、PromptRegistry 和 SkillRegistry，为 LLM 提供完整上下文

架构分层：
1. PromptTemplate (loader.py) - 最底层，负责模板渲染
2. PromptLoader (loader.py) - 中间层，负责从 YAML 加载
3. PromptRegistry (prompt_registry.py) - 最上层，负责注册管理
4. PromptManager (本文件) - 统一入口，整合所有组件
"""

from typing import Optional
from pathlib import Path

from utils.logger import get_logger
from .prompts import get_prompt_loader, get_registry
from .skill_registry import get_skill_registry

logger = get_logger("core.prompt_manager")


class PromptManager:
    """
    提示词管理器 - 统一入口

    架构说明：
    - 使用 PromptLoader 从 YAML 文件加载模板
    - 使用 PromptRegistry 管理已加载的模板
    - 对外提供统一的访问接口
    """

    def __init__(self, templates_dir: str = ""):
        self.prompt_loader = get_prompt_loader(templates_dir)
        self.prompt_registry = get_registry()
        self.skill_registry = get_skill_registry()
        self._system_prompt: Optional[str] = None

    def build_system_prompt(self, **variables) -> str:
        """
        构建完整的系统提示词

        Args:
            **variables: 动态变量（如 environment, user_preferences 等）

        Returns:
            完整的系统提示词字符串
        """
        # 加载核心提示词模块（使用 PromptLoader）
        role = self.prompt_loader.load_template("role", **variables)
        capabilities = self.prompt_loader.load_template(
            "capabilities", **variables)
        tools = self.prompt_loader.load_template("tools", **variables)
        task_strategy = self.prompt_loader.load_template(
            "task_strategy", **variables)

        # 注册到 Registry（便于后续统一管理）
        for name in ["role", "capabilities", "tools", "task_strategy"]:
            config = self.prompt_loader.get_config(name)
            template_obj = self.prompt_loader.get_template_object(name)
            if config and template_obj:
                self.prompt_registry.register(config, template_obj)

        # 获取 skills 上下文
        skills_context = self.skill_registry.get_all_skills_context()

        # 组合完整提示词
        sections = []

        if role:
            sections.append(role)

        if capabilities:
            sections.append(capabilities)

        if tools:
            sections.append(tools)

        if task_strategy:
            sections.append(task_strategy)

        if skills_context:
            sections.append(skills_context)

        system_prompt = "\n\n".join(sections)
        self._system_prompt = system_prompt

        logger.info(f"构建系统提示词完成，共 {len(sections)} 个模块")
        return system_prompt

    def get_system_prompt(self) -> Optional[str]:
        """获取已构建的系统提示词"""
        return self._system_prompt

    def reload_prompts(self, **variables):
        """重新加载所有提示词"""
        self.prompt_loader.reload_all(**variables)
        self.prompt_registry.clear()
        self.skill_registry.discover_skills()
        self._system_prompt = None  # 清空缓存
        logger.info("提示词已重新加载")

    def get_prompt_module(self, name: str, **variables) -> Optional[str]:
        """获取单个提示词模块"""
        return self.prompt_loader.load_template(name, **variables)

    def get_template_object(self, name: str) -> Optional:
        """获取模板对象（高级用法）"""
        return self.prompt_loader.get_template_object(name)

    def clear_cache(self):
        """清空缓存"""
        self.prompt_loader.clear_cache()
        self.prompt_registry.clear()
        self._system_prompt = None


# 全局提示词管理器实例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager(templates_dir: str = "") -> PromptManager:
    """获取全局 PromptManager 实例"""
    global _prompt_manager
    if _prompt_manager is None:
        # 默认 templates 目录
        if not templates_dir:
            templates_dir = str(Path(__file__).parent /
                                "prompts" / "templates")
        _prompt_manager = PromptManager(templates_dir)
    return _prompt_manager


def reset_prompt_manager():
    """重置全局管理器（主要用于测试）"""
    global _prompt_manager
    _prompt_manager = None
