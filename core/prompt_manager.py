"""
提示词管理器 - 统一入口
整合 PromptLoader 和 SkillRegistry，为 LLM 提供完整上下文
"""

from typing import Dict, List, Optional
from pathlib import Path

from utils.logger import get_logger
from .prompts.loader import get_prompt_loader, PromptLoader
from .skill_registry import get_skill_registry

logger = get_logger("core.prompt_manager")


class PromptManager:
    """提示词管理器"""
    
    def __init__(self, templates_dir: str = ""):
        self.prompt_loader = get_prompt_loader(templates_dir)
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
        # 加载核心提示词模块
        role = self.prompt_loader.load_template("role", **variables)
        capabilities = self.prompt_loader.load_template("capabilities", **variables)
        tools = self.prompt_loader.load_template("tools", **variables)
        task_strategy = self.prompt_loader.load_template("task_strategy", **variables)
        
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
        self.skill_registry.discover_skills()
        self._system_prompt = None  # 清空缓存
        logger.info("提示词已重新加载")
    
    def get_prompt_module(self, name: str, **variables) -> Optional[str]:
        """获取单个提示词模块"""
        return self.prompt_loader.load_template(name, **variables)
    
    def clear_cache(self):
        """清空缓存"""
        self.prompt_loader.clear_cache()
        self._system_prompt = None


# 全局提示词管理器实例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager(templates_dir: str = "") -> PromptManager:
    """获取全局 PromptManager 实例"""
    global _prompt_manager
    if _prompt_manager is None:
        # 默认 templates 目录
        if not templates_dir:
            templates_dir = str(Path(__file__).parent / "prompts" / "templates")
        _prompt_manager = PromptManager(templates_dir)
    return _prompt_manager


def reset_prompt_manager():
    """重置全局管理器（主要用于测试）"""
    global _prompt_manager
    _prompt_manager = None
