"""Agent 对外接口模块。

当前主要暴露两类能力：
- `DeepAgentWrapper`：对 deepagents 的封装，提供面向 UI 的流式聊天接口；
- `create_agent(temperature)`：便捷工厂函数，用于在控制器中创建 Agent 实例。
"""

from .deep_agent import DeepAgentWrapper, create_agent

__all__ = ["DeepAgentWrapper", "create_agent"]
