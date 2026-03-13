"""
Skill 注册表模块
实现 OpenAI Skill 规范的注册、发现和管理功能
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.logger import get_logger
from constants.builtin_paths import BuiltinPaths

logger = get_logger("skill_registry")


@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str
    description: str
    version: str = "1"
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """Skill 实体类"""
    id: str
    metadata: SkillMetadata
    instructions: str
    path: Path
    scripts: Dict[str, Path] = field(default_factory=dict)
    assets: Dict[str, Path] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    level: str = "builtin"  # builtin, global, project

    @property
    def skill_md_path(self) -> Path:
        return self.path / "SKILL.md"


class SkillRegistry:
    """
    Skill 注册表
    管理所有已加载的 skills，支持动态发现和执行
    加载顺序：内置 skills -> 全局 skills -> 项目 skills（同名后加载的覆盖先加载的）
    """

    def __init__(self, skills_dir: str = "skills", global_skills_dir: str = "", project_skills_dir: str = ""):
        self.skills_dir = Path(skills_dir)
        self.global_skills_dir = Path(
            global_skills_dir) if global_skills_dir else None
        self.project_skills_dir = Path(
            project_skills_dir) if project_skills_dir else None
        self.skills: Dict[str, Skill] = {}
        self._load_builtin_skills()
        self._discover_skills()

    def _load_builtin_skills(self):
        """加载内置 skills"""
        # 内置 skills 将在初始化时创建
        pass

    def _discover_skills(self):
        """按顺序加载所有 skills：内置 -> 全局 -> 项目"""
        # 1. 内置 skills 目录
        builtin_dirs = [
            self.skills_dir,
            BuiltinPaths.SKILL_ROOT,  # backend/skills
        ]
        for d in builtin_dirs:
            if d.exists():
                self._discover_skills_from_dir(d, level="builtin")

        # 2. 全局 skills 目录（如果配置）
        if self.global_skills_dir and self.global_skills_dir.exists():
            logger.info(f"加载全局 skills: {self.global_skills_dir}")
            self._discover_skills_from_dir(
                self.global_skills_dir, level="global")

        # 3. 项目 skills 目录（如果配置）——项目级覆盖全局
        if self.project_skills_dir and self.project_skills_dir.exists():
            logger.info(f"加载项目 skills: {self.project_skills_dir}")
            self._discover_skills_from_dir(
                self.project_skills_dir, level="project")

    def discover_skills(self):
        """公共方法：重新发现所有 skills"""
        self.skills.clear()
        self._load_builtin_skills()
        self._discover_skills()

    def reload_with_dirs(self, global_skills_dir: str = "", project_skills_dir: str = ""):
        """重新加载，更新全局/项目 skill 目录"""
        self.global_skills_dir = Path(
            global_skills_dir) if global_skills_dir else None
        self.project_skills_dir = Path(
            project_skills_dir) if project_skills_dir else None
        # 清空已加载的 skills
        self.discover_skills()

    def _discover_skills_from_dir(self, skills_dir: Path, level: str = "builtin"):
        """从指定目录发现 skills"""
        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir():
                skill_md = skill_path / "SKILL.md"
                if skill_md.exists():
                    try:
                        self._load_skill(skill_path, level=level)
                    except (yaml.YAMLError, IOError, ValueError) as e:
                        logger.error(f"加载 skill 失败 {skill_path}: {e}")

    def _load_skill(self, skill_path: Path, level: str = "builtin") -> Skill:
        """加载单个 skill"""
        skill_md_path = skill_path / "SKILL.md"
        content = skill_md_path.read_text(encoding='utf-8')

        # 解析 frontmatter 和 instructions
        metadata, instructions = self._parse_skill_md(content)

        # 生成 skill ID
        skill_id = f"skill_{metadata.name}_{metadata.version}"

        # 收集脚本文件
        scripts = {}
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.iterdir():
                if script.is_file():
                    scripts[script.name] = script

        # 收集资源文件
        assets = {}
        assets_dir = skill_path / "assets"
        if assets_dir.exists():
            for asset in assets_dir.rglob("*"):
                if asset.is_file():
                    rel_path = asset.relative_to(assets_dir)
                    assets[str(rel_path)] = asset

        skill = Skill(
            id=skill_id,
            metadata=metadata,
            instructions=instructions,
            path=skill_path,
            scripts=scripts,
            assets=assets,
            level=level
        )

        self.skills[skill_id] = skill
        self.skills[metadata.name] = skill  # 同时用 name 作为 key

        logger.info(f"已加载 skill: {metadata.name} (v{metadata.version})")
        return skill

    def _parse_skill_md(self, content: str) -> tuple[SkillMetadata, str]:
        """解析 SKILL.md 文件"""
        # 匹配 YAML frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            raise ValueError("SKILL.md 格式错误: 缺少 frontmatter")

        frontmatter_str = match.group(1)
        instructions = match.group(2).strip()

        # 解析 YAML
        frontmatter = yaml.safe_load(frontmatter_str)

        metadata = SkillMetadata(
            name=frontmatter.get('name', 'unnamed'),
            description=frontmatter.get('description', ''),
            version=str(frontmatter.get('version', '1')),
            author=frontmatter.get('author'),
            tags=frontmatter.get('tags', []),
            inputs=frontmatter.get('inputs', {}),
            outputs=frontmatter.get('outputs', {})
        )

        return metadata, instructions

    def get_skill(self, skill_id_or_name: str) -> Optional[Skill]:
        """获取指定 skill"""
        return self.skills.get(skill_id_or_name)

    def list_skills(self) -> List[Skill]:
        """列出所有已加载的 skills"""
        # 去重（id 和 name 都指向同一个 skill）
        seen = set()
        result = []
        for skill in self.skills.values():
            if skill.id not in seen:
                seen.add(skill.id)
                result.append(skill)
        return result

    def search_skills(self, query: str) -> List[Skill]:
        """搜索 skills"""
        query = query.lower()
        results = []
        for skill in self.list_skills():
            if (query in skill.metadata.name.lower() or
                query in skill.metadata.description.lower() or
                    any(query in tag.lower() for tag in skill.metadata.tags)):
                results.append(skill)
        return results

    def reload_skill(self, skill_name: str) -> Optional[Skill]:
        """重新加载指定 skill"""
        skill = self.get_skill(skill_name)
        if skill:
            # 从字典中移除旧引用
            del self.skills[skill.id]
            del self.skills[skill.metadata.name]
            # 重新加载
            return self._load_skill(skill.path)
        return None

    def get_skill_context(self, skill_id_or_name: str) -> str:
        """
        获取 skill 的上下文信息，用于注入到 LLM 提示词中
        """
        skill = self.get_skill(skill_id_or_name)
        if not skill:
            return ""

        context = f"""## Skill: {skill.metadata.name}

**描述**: {skill.metadata.description}
**版本**: {skill.metadata.version}

### 使用说明
{skill.instructions}

### 输入参数
"""
        if skill.metadata.inputs:
            for key, value in skill.metadata.inputs.items():
                context += f"- `{key}`: {value}\n"
        else:
            context += "无特定输入参数\n"

        context += "\n### 输出\n"
        if skill.metadata.outputs:
            for key, value in skill.metadata.outputs.items():
                context += f"- `{key}`: {value}\n"
        else:
            context += "根据具体执行结果返回\n"

        # 添加可用脚本信息
        if skill.scripts:
            context += "\n### 可用脚本\n"
            for script_name in skill.scripts.keys():
                context += f"- `{script_name}`\n"

        return context

    def get_all_skills_context(self) -> str:
        """获取所有 skills 的上下文信息"""
        skills = self.list_skills()
        if not skills:
            return ""

        context = "## 可用 Skills\n\n"
        for skill in skills:
            context += f"- **{skill.metadata.name}**: {skill.metadata.description}\n"

        context += "\n当用户需要执行特定任务时，可以使用 `/skill {skill_name}` 格式调用相应 skill。\n"
        return context


# 全局注册表实例
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry(skills_dir: str = "skills") -> SkillRegistry:
    """获取全局 SkillRegistry 实例"""
    global _skill_registry
    if _skill_registry is None:
        # 尝试获取全局 skills 路径
        try:
            from core.config_manager import get_config_manager
            _config = get_config_manager()
            global_skills_dir = _config.get_global_skills_path()
            current_project = _config.get_current_project_path()
            project_skills_dir = str(
                Path(current_project) / "skills") if current_project else ""
        except Exception:
            global_skills_dir = ""
            project_skills_dir = ""

        _skill_registry = SkillRegistry(
            skills_dir=skills_dir,
            global_skills_dir=global_skills_dir,
            project_skills_dir=project_skills_dir
        )
    return _skill_registry


def reset_skill_registry():
    """重置全局注册表（主要用于测试）"""
    global _skill_registry
    _skill_registry = None
