
from pathlib import Path


class BuiltinPaths:

    """内置文件路径"""

    PROJECT_ROOT = Path.cwd()

    LOG_ROOT = PROJECT_ROOT / "logs"

    AGENT_ROOT = PROJECT_ROOT / ".agent"
    CONFIG_ROOT = AGENT_ROOT / "config"
    SESSION_ROOT = AGENT_ROOT / "sessions"
    SKILL_ROOT = AGENT_ROOT / "skills"
    RULE_ROOT = AGENT_ROOT / "rules"
    PLAN_ROOT = AGENT_ROOT / "plans"
    PROMPT_ROOT = AGENT_ROOT / "prompts"
    DB_ROOT = AGENT_ROOT / "db"
