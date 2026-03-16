"""Agent 对外接口模块。

当前主要暴露两类能力：
- `DashengAgent`：基于 LangChain + LangGraph 的自研 Agent（推荐）
- `DeepAgentWrapper`：对 deepagents 的封装（向后兼容，已弃用）
- `create_agent(temperature)`：便捷工厂函数，用于在控制器中创建 Agent 实例。
"""

from .dasheng_agent import DashengAgent, create_agent
from .deep_agent import DeepAgentWrapper  # 向后兼容

__all__ = ["DashengAgent", "create_agent", "DeepAgentWrapper"]
