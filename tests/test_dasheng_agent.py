"""
Dasheng Agent 测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """测试导入"""
    print("=== 测试导入 ===")
    
    try:
        from agent.dasheng_agent import DashengAgent, create_agent
        print("✅ DashengAgent 导入成功")
    except ImportError as e:
        print(f"❌ DashengAgent 导入失败：{e}")
        return False
    
    try:
        from llm.langchain_factory import get_llm
        print("✅ LangChain Factory 导入成功")
    except ImportError as e:
        print(f"❌ LangChain Factory 导入失败：{e}")
        return False
    
    try:
        from core.prompt_manager import get_prompt_manager
        print("✅ Prompt Manager 导入成功")
    except ImportError as e:
        print(f"❌ Prompt Manager 导入失败：{e}")
        return False
    
    return True


def test_agent_structure():
    """测试 Agent 结构（不实际初始化 LLM）"""
    print("\n=== 测试 Agent 结构 ===")
    
    from agent.dasheng_agent import AgentState
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # 测试状态定义
    state = AgentState(
        messages=[HumanMessage(content="test")],
        current_plan=None,
        skills_context="",
        last_response=""
    )
    print(f"✅ AgentState 创建成功")
    print(f"   消息数：{len(state['messages'])}")
    
    return True


def test_prompt_integration():
    """测试 Prompt DSL 集成"""
    print("\n=== 测试 Prompt DSL 集成 ===")
    
    from core.prompt_manager import get_prompt_manager
    
    manager = get_prompt_manager()
    
    # 测试加载提示词
    role = manager.get_prompt_module("role")
    if role:
        print(f"✅ Role 提示词加载成功：{len(role)} 字符")
    else:
        print("⚠️ Role 提示词加载失败")
    
    capabilities = manager.get_prompt_module("capabilities")
    if capabilities:
        print(f"✅ Capabilities 提示词加载成功：{len(capabilities)} 字符")
    
    return True


def main():
    """运行所有测试"""
    print("🐒 Dasheng Agent 测试套件\n")
    
    tests = [
        ("导入测试", test_imports),
        ("结构测试", test_agent_structure),
        ("Prompt 集成测试", test_prompt_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {name} 失败：{e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"测试结果：{passed} 通过，{failed} 失败")
    print(f"{'='*40}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
