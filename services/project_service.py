"""
项目管理服务
负责项目的添加、删除、切换等操作
"""

from typing import Dict, List, Optional
from pathlib import Path

from core.config_manager import get_config_manager
from utils.logger import get_logger

logger = get_logger("services.project")

# 获取配置管理器实例
_config = get_config_manager()


class ProjectService:
    """项目管理服务"""

    def __init__(self):
        pass

    def get_current_project(self) -> Optional[str]:
        """获取当前项目路径"""
        return _config.get_current_project_path()

    def set_current_project(self, project_path: str) -> bool:
        """设置当前项目"""
        try:
            # 验证路径是否存在
            path = Path(project_path)
            if not path.exists():
                logger.error(f"项目路径不存在：{project_path}")
                return False

            if not path.is_dir():
                logger.error(f"项目路径不是目录：{project_path}")
                return False

            # 保存设置
            _config.set_current_project_path(project_path)
            logger.info(f"切换到项目：{path.name}")
            return True

        except Exception as e:
            logger.error(f"设置项目失败：{e}")
            return False

    def get_all_projects(self) -> List[Dict[str, str]]:
        """获取所有项目列表"""
        return _config.get_projects_list()

    def add_project(self, path: str, name: str = "") -> bool:
        """添加项目到列表"""
        try:
            # 验证路径
            path_obj = Path(path)
            if not path_obj.exists():
                logger.error(f"项目路径不存在：{path}")
                return False

            # 如果没有提供名称，使用目录名
            if not name:
                name = path_obj.name

            # 添加到列表
            if _config.add_project(path, name):
                logger.info(f"添加项目：{name} ({path})")
                return True
            else:
                logger.warning(f"项目已存在：{path}")
                return False

        except Exception as e:
            logger.error(f"添加项目失败：{e}")
            return False

    def remove_project(self, path: str) -> bool:
        """从列表中移除项目"""
        try:
            if _config.remove_project(path):
                logger.info(f"移除项目：{path}")

                # 如果移除的是当前项目，清空当前项目
                current = self.get_current_project()
                if current == path:
                    _config.set_current_project_path("")

                return True
            return False

        except Exception as e:
            logger.error(f"移除项目失败：{e}")
            return False

    def get_project_name(self, path: str) -> str:
        """获取项目名称"""
        projects = self.get_all_projects()
        for project in projects:
            if project["path"] == path:
                return project["name"]

        # 如果没有找到，返回目录名
        return Path(path).name

    def is_valid_project(self, path: str) -> bool:
        """验证是否为有效的项目目录"""
        try:
            path_obj = Path(path)

            # 检查是否存在且为目录
            if not path_obj.exists() or not path_obj.is_dir():
                return False

            # 检查是否包含常见的项目文件
            project_indicators = [
                "requirements.txt",  # Python
                "package.json",      # Node.js
                "Cargo.toml",        # Rust
                "go.mod",            # Go
                ".git",              # Git 仓库
                "src",               # 源代码目录
            ]

            for indicator in project_indicators:
                if (path_obj / indicator).exists():
                    return True

            # 如果没有指示文件，至少有代码文件
            code_files = list(path_obj.glob("**/*.py")) + \
                list(path_obj.glob("**/*.js")) + \
                list(path_obj.glob("**/*.ts"))

            return len(code_files) > 0

        except Exception as e:
            logger.error(f"验证项目失败：{e}")
            return False
