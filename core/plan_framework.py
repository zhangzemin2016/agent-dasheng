"""
计划执行框架
支持复杂任务的计划生成、执行、状态管理和失败处理
"""

import json
import uuid
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, AsyncIterator
from dataclasses import dataclass, field, asdict
import asyncio


class PlanStatus(Enum):
    """计划状态"""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    PAUSED = "paused"             # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 执行失败
    CANCELLED = "cancelled"       # 已取消
    ROLLING_BACK = "rolling_back"  # 回滚中
    ROLLED_BACK = "rolled_back"   # 已回滚


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 执行失败
    SKIPPED = "skipped"       # 已跳过
    RETRYING = "retrying"     # 重试中


class PlanAction(str, Enum):
    """计划步骤动作类型

    约定常见类型，便于上层统一使用与静态检查。
    具体 handler 通过 PlanExecutor.register_action_handler 进行绑定。
    """

    TOOL_CALL = "tool_call"
    COMMAND = "command"
    FILE_OPERATION = "file_operation"
    CUSTOM = "custom"


@dataclass
class StepResult:
    """步骤执行结果"""
    success: bool
    output: str = ""
    error: str = ""
    # 结构化附加数据；约定常用键：
    # - "logs": List[str]    该步骤的详细日志
    # - "artifacts": Dict    生成的工件（文件路径、链接等）
    # - "_context_update": Dict  用于更新执行上下文
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0  # 执行耗时（秒）
    # 是否可重试：如果为 False，则在出错时不再进入重试逻辑
    retryable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "data": self.data,
            "execution_time": self.execution_time,
            "retryable": self.retryable,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepResult":
        return cls(**data)


@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    name: str
    description: str
    action: str  # 动作类型: PlanAction 值，如 "tool_call" / "command" 等
    params: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Optional[StepResult] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)  # 依赖的步骤ID
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "action": self.action,
            "params": self.params,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        data = data.copy()
        data["status"] = StepStatus(data["status"])
        if data.get("result"):
            data["result"] = StepResult.from_dict(data["result"])
        return cls(**data)


@dataclass
class ExecutionPlan:
    """执行计划"""
    id: str
    name: str
    description: str
    steps: List[PlanStep]
    status: PlanStatus = PlanStatus.PENDING
    current_step_index: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        data = data.copy()
        data["status"] = PlanStatus(data["status"])
        data["steps"] = [PlanStep.from_dict(s) for s in data["steps"]]
        return cls(**data)

    def get_current_step(self) -> Optional[PlanStep]:
        """获取当前步骤"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def get_step_by_id(self, step_id: str) -> Optional[PlanStep]:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_completed_steps(self) -> List[PlanStep]:
        """获取已完成的步骤"""
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]

    def get_failed_steps(self) -> List[PlanStep]:
        """获取失败的步骤"""
        return [s for s in self.steps if s.status == StepStatus.FAILED]

    def get_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        total = len(self.steps)
        completed = len(self.get_completed_steps())
        failed = len(self.get_failed_steps())
        pending = total - completed - failed

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "percentage": (completed / total * 100) if total > 0 else 0
        }


class PlanStorage:
    """计划存储管理（基于统一数据库）"""

    def __init__(self):
        from storage.database import get_plan_repository
        self._repo = get_plan_repository()

    def save(self, plan: ExecutionPlan) -> None:
        """保存计划"""
        plan_dict = plan.to_dict()
        self._repo.save(plan_dict)

    def load(self, plan_id: str) -> Optional[ExecutionPlan]:
        """加载计划"""
        data = self._repo.load(plan_id)
        if not data:
            return None
        return ExecutionPlan.from_dict(data)

    def list_plans(self, project_path: str = None) -> List[Dict[str, Any]]:
        """列出所有计划"""
        return self._repo.list_all(project_path)

    def delete(self, plan_id: str) -> bool:
        """删除计划"""
        return self._repo.delete(plan_id)


class PlanExecutor:
    """计划执行器"""

    def __init__(self, storage: PlanStorage = None):
        self.storage = storage or PlanStorage()
        # 动作处理器映射：key 为 PlanAction.value 或兼容的字符串
        self._action_handlers: Dict[str, Callable] = {}
        self._current_plan: Optional[ExecutionPlan] = None
        self._stop_requested = False
        self._execution_context: Dict[str, Any] = {}  # 执行上下文，用于步骤间共享数据

    def register_action_handler(self, action: Any, handler: Callable) -> None:
        """注册动作处理器

        Args:
            action: PlanAction 或其对应的字符串值。
            handler: 协程函数，签名为 async def handler(params: Dict[str, Any]) -> StepResult
        """
        key = action.value if isinstance(action, PlanAction) else str(action)
        self._action_handlers[key] = handler

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        on_step_start: Callable[[PlanStep], None] = None,
        on_step_complete: Callable[[PlanStep, StepResult], None] = None,
        on_step_failed: Callable[[PlanStep, StepResult], None] = None,
        on_progress: Callable[[Dict[str, Any]], None] = None,
        execution_context: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        """
        执行计划

        Args:
            plan: 执行计划
            on_step_start: 步骤开始回调
            on_step_complete: 步骤完成回调
            on_step_failed: 步骤失败回调
            on_progress: 进度更新回调
            execution_context: 执行上下文，用于步骤间共享数据

        Yields:
            执行过程中的反馈信息
        """
        self._current_plan = plan
        self._stop_requested = False
        self._execution_context = execution_context or {}

        # 更新计划状态
        plan.status = PlanStatus.RUNNING
        plan.started_at = datetime.now().isoformat()
        self.storage.save(plan)

        yield f"🚀 开始执行计划: {plan.name}\n"
        yield f"📋 共 {len(plan.steps)} 个步骤\n\n"

        try:
            while plan.current_step_index < len(plan.steps):
                if self._stop_requested:
                    plan.status = PlanStatus.CANCELLED
                    yield "\n⏹️ 计划执行已取消\n"
                    break

                step = plan.steps[plan.current_step_index]

                # 检查依赖
                if not await self._check_dependencies(step, plan):
                    yield f"⏭️ 步骤 '{step.name}' 的依赖未完成，跳过\n"
                    step.status = StepStatus.SKIPPED
                    plan.current_step_index += 1
                    continue

                # 执行步骤
                async for msg in self._execute_step(
                    step, plan,
                    on_step_start, on_step_complete, on_step_failed
                ):
                    yield msg

                # 更新进度
                progress = plan.get_progress()
                if on_progress:
                    on_progress(progress)

                yield f"\n📊 进度: {progress['completed']}/{progress['total']} ({progress['percentage']:.1f}%)\n"

                # 保存状态
                self.storage.save(plan)

                # 检查是否需要停止
                if step.status == StepStatus.FAILED and step.retry_count >= step.max_retries:
                    plan.status = PlanStatus.FAILED
                    yield f"\n❌ 计划执行失败: 步骤 '{step.name}' 达到最大重试次数\n"
                    break

                plan.current_step_index += 1

            # 完成处理
            if plan.status == PlanStatus.RUNNING:
                plan.status = PlanStatus.COMPLETED
                plan.completed_at = datetime.now().isoformat()
                yield f"\n✅ 计划执行完成！\n"

        except Exception as e:
            plan.status = PlanStatus.FAILED
            yield f"\n💥 计划执行异常: {str(e)}\n"

        finally:
            self.storage.save(plan)
            self._current_plan = None

    async def _check_dependencies(self, step: PlanStep, plan: ExecutionPlan) -> bool:
        """检查步骤依赖是否满足"""
        if not step.dependencies:
            return True

        for dep_id in step.dependencies:
            dep_step = plan.get_step_by_id(dep_id)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        return True

    async def _execute_step(
        self,
        step: PlanStep,
        plan: ExecutionPlan,
        on_start: Callable = None,
        on_complete: Callable = None,
        on_failed: Callable = None
    ) -> AsyncIterator[str]:
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now().isoformat()

        yield f"\n📍 步骤 {plan.current_step_index + 1}/{len(plan.steps)}: {step.name}\n"
        yield f"📝 {step.description}\n"

        if on_start:
            on_start(step)

        start_time = asyncio.get_event_loop().time()

        try:
            # 获取动作处理器；兼容 PlanAction 和字符串两种写法
            handler = self._action_handlers.get(step.action)
            if not handler:
                raise ValueError(f"未找到动作处理器: {step.action}")

            # 构建执行参数，注入上下文
            params = step.params.copy()
            params['_execution_context'] = self._execution_context
            params['_step_id'] = step.id
            params['_plan_id'] = plan.id

            # 执行动作
            result = await handler(params)

            execution_time = asyncio.get_event_loop().time() - start_time

            if result.success:
                step.status = StepStatus.COMPLETED
                step.result = result
                step.completed_at = datetime.now().isoformat()

                # 更新执行上下文（如果结果包含上下文更新）
                if result.data and '_context_update' in result.data:
                    self._execution_context.update(
                        result.data['_context_update'])

                yield f"✅ 步骤完成 ({execution_time:.2f}s)\n"
                if result.output:
                    yield f"📤 {result.output}\n"

                if on_complete:
                    on_complete(step, result)
            else:
                raise Exception(result.error or "执行失败")

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time

            step.retry_count += 1

            error_msg = str(e)
            # 默认认为错误是可重试的，除非已有 result 且明确标记为不可重试
            existing_retryable = (
                step.result.retryable  # type: ignore[union-attr]
                if isinstance(step.result, StepResult)
                else True
            )
            step.result = StepResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                retryable=existing_retryable,
            )

            # 不可重试的错误，直接标记为失败
            if not step.result.retryable:
                step.status = StepStatus.FAILED
                yield f"❌ 步骤失败（不可重试）: {error_msg}\n"
                if on_failed:
                    on_failed(step, step.result)
                return

            if step.retry_count < step.max_retries:
                step.status = StepStatus.RETRYING
                yield f"⚠️ 步骤失败，准备重试 ({step.retry_count}/{step.max_retries}): {error_msg}\n"
            else:
                step.status = StepStatus.FAILED
                yield f"❌ 步骤失败 (已达最大重试次数): {error_msg}\n"

                if on_failed:
                    on_failed(step, step.result)

    def pause(self) -> None:
        """暂停执行"""
        if self._current_plan:
            self._current_plan.status = PlanStatus.PAUSED
            self.storage.save(self._current_plan)

    def resume(self) -> None:
        """恢复执行"""
        if self._current_plan and self._current_plan.status == PlanStatus.PAUSED:
            self._current_plan.status = PlanStatus.RUNNING

    def stop(self) -> None:
        """停止执行"""
        self._stop_requested = True

    async def rollback_plan(self, plan: ExecutionPlan) -> AsyncIterator[str]:
        """回滚计划"""
        if plan.status not in [PlanStatus.FAILED, PlanStatus.COMPLETED]:
            yield "⚠️ 只能回滚已完成或失败的计划\n"
            return

        plan.status = PlanStatus.ROLLING_BACK
        yield f"🔄 开始回滚计划: {plan.name}\n"

        # 逆序回滚已完成的步骤
        completed_steps = [
            s for s in plan.steps if s.status == StepStatus.COMPLETED]

        for step in reversed(completed_steps):
            yield f"⏪ 回滚步骤: {step.name}\n"
            # TODO: 实现具体的回滚逻辑
            step.status = StepStatus.PENDING

        plan.status = PlanStatus.ROLLED_BACK
        plan.completed_at = datetime.now().isoformat()
        self.storage.save(plan)

        yield "✅ 计划回滚完成\n"


class PlanManager:
    """计划管理器"""

    def __init__(self):
        self.storage = PlanStorage()
        self.executor = PlanExecutor(self.storage)
        self._active_plans: Dict[str, ExecutionPlan] = {}  # 活跃计划缓存

    def create_plan(
        self,
        name: str,
        description: str,
        steps_data: List[Dict[str, Any]],
        *,
        session_id: Optional[str] = None,
        project_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """创建新计划"""
        steps = []
        for i, step_data in enumerate(steps_data):
            step = PlanStep(
                id=step_data.get("id") or f"step_{i+1}",
                name=step_data["name"],
                description=step_data["description"],
                action=step_data["action"],
                params=step_data.get("params", {}),
                max_retries=step_data.get("max_retries", 3),
                dependencies=step_data.get("dependencies", [])
            )
            steps.append(step)

        plan = ExecutionPlan(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            steps=steps,
            metadata=metadata or {},
        )

        # 将会话和项目信息写入 metadata，便于后续按会话/项目筛选和展示
        if session_id:
            plan.metadata.setdefault("session_id", session_id)
        if project_path:
            plan.metadata.setdefault("project_path", project_path)

        self.storage.save(plan)
        self._active_plans[plan.id] = plan
        return plan

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """获取计划"""
        # 先从缓存获取
        if plan_id in self._active_plans:
            return self._active_plans[plan_id]
        # 从存储加载
        plan = self.storage.load(plan_id)
        if plan:
            self._active_plans[plan_id] = plan
        return plan

    def list_plans(self) -> List[Dict[str, Any]]:
        """列出所有计划"""
        return self.storage.list_plans()

    def delete_plan(self, plan_id: str) -> bool:
        """删除计划"""
        if plan_id in self._active_plans:
            del self._active_plans[plan_id]
        return self.storage.delete(plan_id)

    async def execute(
        self,
        plan: ExecutionPlan,
        **kwargs
    ) -> AsyncIterator[str]:
        """执行计划"""
        # 确保计划在活跃缓存中
        self._active_plans[plan.id] = plan
        async for msg in self.executor.execute_plan(plan, **kwargs):
            yield msg

    def pause_plan(self, plan_id: str) -> bool:
        """暂停计划"""
        plan = self.get_plan(plan_id)
        if plan and plan.status == PlanStatus.RUNNING:
            self.executor.pause()
            return True
        return False

    def resume_plan(self, plan_id: str) -> bool:
        """恢复计划"""
        plan = self.get_plan(plan_id)
        if plan and plan.status == PlanStatus.PAUSED:
            self.executor.resume()
            return True
        return False

    def stop_plan(self, plan_id: str) -> bool:
        """停止计划"""
        plan = self.get_plan(plan_id)
        if plan and plan.status in [PlanStatus.RUNNING, PlanStatus.PAUSED]:
            self.executor.stop()
            return True
        return False

    async def resume_execution(
        self,
        plan_id: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """从上次中断处恢复执行计划"""
        plan = self.get_plan(plan_id)
        if not plan:
            yield f"❌ 未找到计划: {plan_id}\n"
            return

        if plan.status not in [PlanStatus.PAUSED, PlanStatus.FAILED]:
            yield f"⚠️ 计划状态不允许恢复: {plan.status.value}\n"
            return

        # 恢复计划状态
        plan.status = PlanStatus.RUNNING
        self.storage.save(plan)

        yield f"🔄 恢复执行计划: {plan.name}\n"
        yield f"📍 从步骤 {plan.current_step_index + 1}/{len(plan.steps)} 继续\n\n"

        # 继续执行
        async for msg in self.executor.execute_plan(plan, **kwargs):
            yield msg

    def get_plan_summary(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取计划摘要（用于UI展示）"""
        plan = self.get_plan(plan_id)
        if not plan:
            return None

        return {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "status": plan.status.value,
            "progress": plan.get_progress(),
            "current_step": plan.current_step_index,
            "total_steps": len(plan.steps),
            "created_at": plan.created_at,
            "started_at": plan.started_at,
            "completed_at": plan.completed_at,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "action": s.action,
                    "retry_count": s.retry_count,
                    "execution_time": s.result.execution_time if s.result else 0
                }
                for s in plan.steps
            ]
        }


# 全局计划管理器实例
_plan_manager: Optional[PlanManager] = None


def get_plan_manager() -> PlanManager:
    """获取计划管理器实例"""
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = PlanManager()
    return _plan_manager
