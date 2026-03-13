"""
Rules 管理模块
支持从项目路径的 rules 目录加载和管理规则文件
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from utils.logger import get_logger
from constants.builtin_paths import BuiltinPaths

logger = get_logger("utils.rules_manager")


@dataclass
class Rule:
    """规则数据类"""
    name: str
    description: str
    content: str
    file_path: str
    priority: int = 0
    enabled: bool = True
    level: str = "project"  # builtin, global, project


class RulesManager:
    """规则管理器 - 支持三级规则：内置、全局、项目"""

    def __init__(self, project_path: str, global_rules_dir: str = ""):
        self.project_path = project_path
        self.rules_dir = Path(project_path) / "rules" if project_path else None
        self.global_rules_dir = Path(
            global_rules_dir) if global_rules_dir else None
        self.rules: List[Rule] = []

    def ensure_rules_dir(self) -> bool:
        """确保 rules 目录存在"""
        if not self.rules_dir:
            return False
        try:
            self.rules_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建 rules 目录失败: {e}")
            return False

    def get_rules_dir(self) -> Optional[Path]:
        """获取 rules 目录路径"""
        return self.rules_dir

    def list_rules(self) -> List[Rule]:
        """列出所有规则，按级别分组：内置 -> 全局 -> 项目"""
        self.rules = []

        # 1. 加载内置规则（从应用目录）
        builtin_dir = BuiltinPaths.RULE_ROOT
        if builtin_dir.exists():
            for file_path in sorted(builtin_dir.glob("*.md")):
                try:
                    rule = self._parse_rule_file(file_path, level="builtin")
                    if rule:
                        self.rules.append(rule)
                except Exception as e:
                    logger.error(f"解析内置规则失败 {file_path}: {e}")

        # 2. 加载全局规则
        if self.global_rules_dir and self.global_rules_dir.exists():
            for file_path in sorted(self.global_rules_dir.glob("*.md")):
                try:
                    rule = self._parse_rule_file(file_path, level="global")
                    if rule:
                        self.rules.append(rule)
                except Exception as e:
                    logger.error(f"解析全局规则失败 {file_path}: {e}")

        # 3. 加载项目规则
        if self.rules_dir and self.rules_dir.exists():
            for file_path in sorted(self.rules_dir.glob("*.md")):
                try:
                    rule = self._parse_rule_file(file_path, level="project")
                    if rule:
                        self.rules.append(rule)
                except Exception as e:
                    logger.error(f"解析项目规则失败 {file_path}: {e}")

        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return self.rules

    def _parse_rule_file(self, file_path: Path, level: str = "project") -> Optional[Rule]:
        """解析规则文件"""
        content = file_path.read_text(encoding='utf-8')

        # 解析 frontmatter
        name = file_path.stem
        description = ""
        priority = 0
        enabled = True

        # 匹配 frontmatter
        frontmatter_match = re.match(
            r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # 解析 name
            name_match = re.search(
                r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
            if name_match:
                name = name_match.group(1).strip()
            # 解析 description
            desc_match = re.search(
                r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
            if desc_match:
                description = desc_match.group(1).strip()
            # 解析 priority
            priority_match = re.search(
                r'^priority:\s*(\d+)$', frontmatter, re.MULTILINE)
            if priority_match:
                priority = int(priority_match.group(1))
            # 解析 enabled
            enabled_match = re.search(
                r'^enabled:\s*(true|false)$', frontmatter, re.MULTILINE | re.IGNORECASE)
            if enabled_match:
                enabled = enabled_match.group(1).lower() == 'true'

        return Rule(
            name=name,
            description=description,
            content=content,
            file_path=str(file_path),
            priority=priority,
            enabled=enabled,
            level=level
        )

    def get_rule(self, name: str) -> Optional[Rule]:
        """获取指定规则"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def save_rule(self, name: str, description: str, content: str, priority: int = 0, enabled: bool = True) -> bool:
        """保存规则"""
        if not self.ensure_rules_dir():
            return False

        try:
            # 生成文件名
            file_name = f"{name.lower().replace(' ', '_')}.md"
            file_path = self.rules_dir / file_name

            # 构建 frontmatter
            frontmatter = f"""---
name: {name}
description: {description}
priority: {priority}
enabled: {str(enabled).lower()}
---

"""
            # 如果 content 已经有 frontmatter，去掉它
            content_clean = re.sub(
                r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)

            # 写入文件
            full_content = frontmatter + content_clean
            file_path.write_text(full_content, encoding='utf-8')

            logger.info(f"规则已保存: {file_path}")
            return True
        except Exception as e:
            logger.error(f"保存规则失败: {e}")
            return False

    def delete_rule(self, name: str) -> bool:
        """删除规则"""
        rule = self.get_rule(name)
        if not rule:
            return False

        try:
            Path(rule.file_path).unlink()
            logger.info(f"规则已删除: {rule.file_path}")
            return True
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            return False

    def get_enabled_rules_content(self) -> str:
        """获取所有启用的规则内容（合并）"""
        enabled_rules = [r for r in self.rules if r.enabled]
        if not enabled_rules:
            return ""

        contents = []
        for rule in enabled_rules:
            # 去掉 frontmatter
            content_clean = re.sub(
                r'^---\s*\n.*?\n---\s*\n', '', rule.content, flags=re.DOTALL)
            contents.append(f"## {rule.name}\n{content_clean}")

        return "\n\n".join(contents)


def get_rules_manager(project_path: str, global_rules_dir: str = "") -> RulesManager:
    """获取规则管理器实例"""
    return RulesManager(project_path, global_rules_dir)
