"""
统一配置管理器
合并 LLM 配置、应用配置、UI 配置于一体
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger("core.config")

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 配置目录（应用根目录下的 config 文件夹）
CONFIG_DIR = PROJECT_ROOT / "config"

# 配置文件
LLM_CONFIG_FILE = CONFIG_DIR / "llm_config.json"
APP_CONFIG_FILE = CONFIG_DIR / "app_config.json"


class ConfigManager:
    """统一配置管理器"""

    # 默认 LLM 配置
    _DEFAULT_LLM_CONFIG = {
        "provider": "ollama",
        "temperature": 0.7,
        "providers": {
            "deepseek": {
                "model": "deepseek-chat",
                "api_key": "",
                "_type": "builtin",  # builtin | custom
            },
            "ollama": {
                "model": "llama2",
                "base_url": "http://localhost:11434",
                "_type": "builtin",
            },
            "openai": {
                "model": "gpt-3.5-turbo",
                "api_key": "",
                "_type": "builtin",
            },
        }
    }

    # 默认应用配置
    _DEFAULT_APP_CONFIG = {
        "current_project_path": "",
        "projects_list": [],
        "global_skills_dir": "",
        "window": {
            "width": 1400,
            "height": 900,
            "min_width": 800,
            "min_height": 600,
        },
        "ui": {
            "theme": "dark",
            "chat_layout": "full",  # full, sidebar, inline
        }
    }

    def __init__(self):
        self._llm_config: Optional[Dict[str, Any]] = None
        self._app_config: Optional[Dict[str, Any]] = None

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # ========== LLM 配置管理 ==========

    def _load_llm_config_from_file(self) -> Dict[str, Any]:
        """从文件加载 LLM 配置"""
        if LLM_CONFIG_FILE.exists():
            try:
                with open(LLM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载 LLM 配置失败：{e}")
        return {}

    def _save_llm_config_to_file(self, config: Dict[str, Any]):
        """保存 LLM 配置到文件"""
        self._ensure_config_dir()
        with open(LLM_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get_llm_settings(self) -> Dict[str, Any]:
        """获取 LLM 设置（合并默认值、文件配置）"""
        if self._llm_config is not None:
            return self._llm_config

        config = self._DEFAULT_LLM_CONFIG.copy()

        # 从文件加载
        file_config = self._load_llm_config_from_file()
        config.update(file_config)

        self._llm_config = config
        return config

    def save_llm_settings(self, config: Dict[str, Any]):
        """保存 LLM 设置"""
        self._save_llm_config_to_file(config)
        self._llm_config = None  # 清空缓存，下次重新加载

    def is_llm_configured(self) -> bool:
        """检查 LLM 是否已配置"""
        config = self.get_llm_settings()
        provider = config.get("provider", "")
        provider_config = config.get("providers", {}).get(provider, {})

        # 检查是否有模型配置
        model = provider_config.get("model", "")
        if not model:
            return False

        # 对于需要 API key 的提供商
        if provider in ["deepseek", "openai"]:
            api_key = provider_config.get("api_key", "")
            if not api_key:
                return False

        return True

    def get_llm_config(self, provider: str = None) -> dict:
        """获取指定提供商的 LLM 配置"""
        config = self.get_llm_settings()
        provider = provider or config.get("provider", "")
        return config["providers"].get(provider, {})

    # ========== 模型提供商管理 ==========

    def get_builtin_providers(self) -> list:
        """获取内置的模型提供商列表（从配置中读取）"""
        config = self.get_llm_settings()
        providers = config.get("providers", {})
        return [
            pid for pid, pconfig in providers.items()
            if pconfig.get("_type") == "builtin"
        ]

    def get_all_providers(self) -> list:
        """获取所有模型提供商列表（包含内置和自定义）"""
        config = self.get_llm_settings()
        return list(config.get("providers", {}).keys())

    def add_provider(self, provider_id: str, provider_config: dict) -> bool:
        """
        添加新的模型提供商

        Args:
            provider_id: 厂商标识符（如 'zhipu', 'moonshot'）
            provider_config: 厂商配置（包含 model, api_key/base_url 等）

        Returns:
            bool: 是否添加成功
        """
        config = self.get_llm_settings()
        providers = config.get("providers", {})

        # 检查是否已存在
        if provider_id in providers:
            logger.warning(f"提供商 {provider_id} 已存在")
            return False

        # 添加新提供商，默认为 custom 类型
        provider_config["_type"] = "custom"
        providers[provider_id] = provider_config
        config["providers"] = providers
        self.save_llm_settings(config)

        logger.info(f"添加模型提供商：{provider_id}")
        return True
        return True

    def update_provider(self, provider_id: str, provider_config: dict) -> bool:
        """
        更新模型提供商配置

        Args:
            provider_id: 厂商标识符
            provider_config: 新的厂商配置

        Returns:
            bool: 是否更新成功
        """
        config = self.get_llm_settings()
        providers = config.get("providers", {})

        # 检查是否存在
        if provider_id not in providers:
            logger.warning(f"提供商 {provider_id} 不存在")
            return False

        # 保留原有的 _type 属性
        existing_type = providers[provider_id].get("_type", "custom")
        provider_config["_type"] = existing_type

        # 更新配置
        providers[provider_id] = provider_config
        config["providers"] = providers
        self.save_llm_settings(config)

        logger.info(f"更新模型提供商：{provider_id}")
        return True
        self.save_llm_settings(config)

        logger.info(f"更新模型提供商：{provider_id}")
        return True

    def remove_provider(self, provider_id: str) -> bool:
        """
        删除模型提供商

        Args:
            provider_id: 厂商标识符

        Returns:
            bool: 是否删除成功
        """
        config = self.get_llm_settings()
        providers = config.get("providers", {})

        # 检查是否存在
        if provider_id not in providers:
            logger.warning(f"提供商 {provider_id} 不存在")
            return False

        # 不允许删除内置提供商
        if providers[provider_id].get("_type") == "builtin":
            logger.error(f"不允许删除内置提供商：{provider_id}")
            return False

        # 如果当前使用的是该提供商，切换到第一个内置提供商
        if config.get("provider") == provider_id:
            builtin_providers = self.get_builtin_providers()
            if builtin_providers:
                config["provider"] = builtin_providers[0]

        # 删除提供商
        del providers[provider_id]
        config["providers"] = providers
        self.save_llm_settings(config)

        logger.info(f"删除模型提供商：{provider_id}")
        return True

    def get_provider_display_name(self, provider_id: str) -> str:
        """获取提供商的显示名称"""
        display_names = {
            "deepseek": "DeepSeek",
            "ollama": "Ollama (本地)",
            "openai": "OpenAI",
        }
        return display_names.get(provider_id, provider_id.upper())

    # ========== 应用配置管理 ==========

    def _load_app_config_from_file(self) -> Dict[str, Any]:
        """从文件加载应用配置"""
        if APP_CONFIG_FILE.exists():
            try:
                with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载应用配置失败：{e}")
        return {}

    def _save_app_config_to_file(self, config: Dict[str, Any]):
        """保存应用配置到文件"""
        self._ensure_config_dir()
        with open(APP_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def get_app_settings(self) -> Dict[str, Any]:
        """获取应用设置"""
        if self._app_config is not None:
            return self._app_config

        config = self._DEFAULT_APP_CONFIG.copy()

        # 从文件加载
        file_config = self._load_app_config_from_file()
        config.update(file_config)

        self._app_config = config
        return config

    def save_app_settings(self, config: Dict[str, Any]):
        """保存应用设置"""
        self._save_app_config_to_file(config)
        self._app_config = None  # 清空缓存，下次重新加载

    # ========== 便捷方法 ==========

    def get_current_project_path(self) -> str:
        """获取当前项目路径"""
        config = self.get_app_settings()
        return config.get("current_project_path", "")

    def set_current_project_path(self, path: str):
        """设置当前项目路径"""
        config = self.get_app_settings()
        config["current_project_path"] = path
        self.save_app_settings(config)

    def get_projects_list(self) -> list:
        """获取项目列表"""
        config = self.get_app_settings()
        return config.get("projects_list", [])

    def set_projects_list(self, projects: list):
        """设置项目列表"""
        config = self.get_app_settings()
        config["projects_list"] = projects
        self.save_app_settings(config)

    def add_project(self, path: str, name: str) -> bool:
        """添加项目到列表"""
        projects = self.get_projects_list()

        # 检查是否已存在
        if any(p["path"] == path for p in projects):
            return False

        projects.append({"path": path, "name": name})
        self.set_projects_list(projects)
        return True

    def remove_project(self, path: str) -> bool:
        """从列表移除项目"""
        projects = self.get_projects_list()
        original_len = len(projects)
        projects = [p for p in projects if p["path"] != path]

        if len(projects) < original_len:
            self.set_projects_list(projects)

            # 如果移除的是当前项目，清空当前项目
            if self.get_current_project_path() == path:
                self.set_current_project_path("")

            return True
        return False

    def get_global_skills_dir(self) -> str:
        """获取全局技能目录"""
        config = self.get_app_settings()
        return config.get("global_skills_dir", "")

    def set_global_skills_dir(self, path: str):
        """设置全局技能目录"""
        config = self.get_app_settings()
        config["global_skills_dir"] = path
        self.save_app_settings(config)

    def get_global_skills_path(self) -> str:
        """获取全局 skills 子目录路径"""
        base = self.get_global_skills_dir()
        if base:
            return str(Path(base) / "skills")
        return ""

    def get_global_rules_path(self) -> str:
        """获取全局 rules 子目录路径"""
        base = self.get_global_skills_dir()
        if base:
            return str(Path(base) / "rules")
        return ""

    def get_window_settings(self) -> Dict[str, int]:
        """获取窗口设置"""
        config = self.get_app_settings()
        return config.get("window", self._DEFAULT_APP_CONFIG["window"])

    def get_ui_settings(self) -> Dict[str, str]:
        """获取 UI 设置"""
        config = self.get_app_settings()
        return config.get("ui", self._DEFAULT_APP_CONFIG["ui"])

    def set_ui_setting(self, key: str, value: str):
        """设置 UI 配置项"""
        config = self.get_app_settings()
        if "ui" not in config:
            config["ui"] = {}
        config["ui"][key] = value
        self.save_app_settings(config)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
