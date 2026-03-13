"""
主控制器
协调 UI 和业务逻辑的核心控制器
"""

import asyncio
import re
from typing import List, Optional, Dict
from pathlib import Path

import flet as ft

from services.session_service import SessionService
from services.project_service import ProjectService
from core.config_manager import get_config_manager
from agent import create_agent
from utils.logger import get_logger

logger = get_logger("controllers.main")


class MainController:
    """主控制器类"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.session_service = SessionService()
        self.project_service = ProjectService()
        self._config = get_config_manager()  # 获取配置管理器实例
        self.agent = None
        self.is_generating = False
        self._stop_requested = False
        self._current_plan_id: Optional[str] = None  # 当前执行的计划 ID

        # 初始化 Agent (使用 DeepAgents 框架)
        try:
            if self._config.is_llm_configured():
                self.agent = create_agent(temperature=0.7)
                if self.agent.is_ready:
                    logger.info("DeepAgent 初始化成功")
                else:
                    logger.warning("DeepAgent 初始化未完成，请检查 LLM 配置")
            else:
                logger.warning("LLM 未配置，无法初始化 Agent")
        except Exception as e:
            logger.error(f"DeepAgent 初始化失败：{e}")

    def init(self):
        """初始化控制器"""
        # 从存储加载历史会话
        self.load_all_sessions_from_storage()

        # 如果没有历史会话，创建默认会话
        if not self.session_service.sessions:
            self.session_service.create_session()

        logger.info("控制器初始化完成")

    async def handle_user_message(
        self,
        content: str,
        add_user_message_callback,
        add_ai_message_callback,
        update_ui_callback
    ):
        """
        处理用户消息

        Args:
            content: 用户输入内容
            add_user_message_callback: 添加用户消息的回调（仅 UI）
            add_ai_message_callback: 添加 AI 消息的回调（返回 bubble 对象）
            update_ui_callback: 更新 UI 的回调
        """
        if not content.strip():
            return

        if not self.agent:
            logger.error("Agent 未初始化")
            raise RuntimeError("Agent 未初始化，请先配置 LLM")

        # 1. 先保存用户消息到存储
        self.session_service.add_message("user", content)

        # 2. 再添加到 UI 显示
        add_user_message_callback(content)

        # 准备历史记录
        session = self.session_service.get_current_session()
        messages = session["messages"] if session else []

        project_path = self.project_service.get_current_project() or ""

        # 3. 添加 AI 消息占位到存储
        self.session_service.add_message("assistant", "")

        # 4. 添加 AI 消息到 UI（思考状态）
        ai_bubble = add_ai_message_callback("", thinking=True)

        # 流式响应
        message_index = len(messages) - 1  # 最后一条消息的索引

        try:
            async for chunk in self.agent.stream_chat(
                content, project_path
            ):
                if self._stop_requested:
                    break

                # 追加文本到气泡
                ai_bubble.append_text(chunk)

                # 更新会话中的消息
                current_messages = self.session_service.get_current_session()[
                    "messages"]
                if message_index < len(current_messages):
                    current_messages[message_index]["content"] += chunk

                # 更新 UI
                update_ui_callback()
                await asyncio.sleep(0.01)

            # 标记为完成
            if self.session_service.get_current_session():
                current_messages = self.session_service.get_current_session()[
                    "messages"]
                if message_index < len(current_messages):
                    current_messages[message_index]["completed"] = True

            update_ui_callback()

            # 保存会话并生成摘要
            self.save_current_session_with_summary()

        except asyncio.CancelledError:
            logger.info("流式响应任务被取消")
            if ai_bubble:
                ai_bubble.append_text("\n[已中断]")
        except Exception as e:
            logger.error(f"流式响应错误：{e}")
            if ai_bubble:
                ai_bubble.append_text(f"\n[错误：{e}]")
        finally:
            self.is_generating = False
            self._stop_requested = False

    def request_stop(self):
        """请求停止生成"""
        self._stop_requested = True
        self.is_generating = False

        # 如果有正在执行的计划，停止计划
        if self._current_plan_id and self.agent:
            try:
                self.agent.stop_plan(self._current_plan_id)
                logger.info(f"停止计划执行：{self._current_plan_id}")
            except Exception as e:
                logger.error(f"停止计划失败：{e}")

        logger.info("收到停止请求")

    def pause_current_plan(self) -> bool:
        """暂停当前计划"""
        if not self._current_plan_id or not self.agent:
            return False

        try:
            success = self.agent.pause_plan(self._current_plan_id)
            if success:
                logger.info(f"暂停计划：{self._current_plan_id}")
            return success
        except Exception as e:
            logger.error(f"暂停计划失败：{e}")
            return False

    def resume_current_plan(self) -> bool:
        """恢复当前计划"""
        if not self._current_plan_id or not self.agent:
            return False

        try:
            success = self.agent.resume_plan(self._current_plan_id)
            if success:
                logger.info(f"恢复计划：{self._current_plan_id}")
            return success
        except Exception as e:
            logger.error(f"恢复计划失败：{e}")
            return False

    def get_current_plan_status(self) -> Optional[Dict]:
        """获取当前计划状态"""
        if not self._current_plan_id or not self.agent:
            return None

        try:
            return self.agent.get_plan_status(self._current_plan_id)
        except Exception as e:
            logger.error(f"获取计划状态失败：{e}")
            return None

    def list_active_plans(self) -> List[Dict]:
        """获取活跃计划列表"""
        if not self.agent:
            return []

        try:
            return self.agent.get_current_active_plans()
        except Exception as e:
            logger.error(f"获取活跃计划失败：{e}")
            return []

    def get_plan_control_commands(self) -> List[str]:
        """获取计划控制命令列表"""
        return ["/plan pause", "/plan resume", "/plan stop", "/plan status", "/plan list"]

    def create_new_session(self) -> Dict:
        """创建新会话"""
        session = self.session_service.create_session()
        logger.info(f"新建会话：{session['id'][:8]}")
        return session

    def switch_session(self, session_id: str) -> bool:
        """切换会话"""
        success = self.session_service.set_current_session(session_id)
        if success:
            logger.info(f"切换到会话：{session_id[:8]}")
        return success

    def delete_session(self, session_id: str) -> bool:
        """删除会话（包括摘要文件）"""
        # 先从内存中删除
        success = self.session_service.delete_session(session_id)
        if success:
            logger.info(f"删除会话：{session_id[:8]}")
            # 同时从存储中删除（包括摘要文件）
            from storage.session_storage import get_session_storage
            storage = get_session_storage()
            storage.delete_session(session_id)
        return success

    def get_current_messages(self) -> List[Dict]:
        """获取当前会话的消息列表"""
        session = self.session_service.get_current_session()
        return session["messages"] if session else []

    def load_current_messages(self) -> List[Dict]:
        """加载并返回当前会话的完整消息（包含 completed 状态）"""
        session = self.session_service.get_current_session()
        if not session:
            return []

        # 确保最后一条消息的 completed 状态正确
        messages = session["messages"]
        if messages and not messages[-1].get("completed", True):
            # 如果最后一条未完成，标记为思考中状态
            logger.debug(f"检测到未完成的 AI 消息，将显示思考状态")

        return messages

    def get_all_sessions(self) -> List[Dict]:
        """获取所有会话"""
        return self.session_service.get_all_sessions()

    def save_current_session_with_summary(self) -> bool:
        """保存当前会话并生成摘要"""
        session = self.session_service.get_current_session()
        if not session:
            logger.error("没有当前会话")
            return False

        # 保存到存储
        from storage.session_storage import get_session_storage
        storage = get_session_storage()

        if not storage.save_session(session):
            logger.error("保存会话失败")
            return False

        # 生成并保存摘要
        summary = self.session_service.generate_summary(session["id"])
        if summary:
            storage.save_session_summary(session["id"], summary)
            logger.info(f"已保存会话摘要：{session['id'][:8]}")

        return True

    def get_current_project(self) -> Optional[str]:
        """获取当前项目"""
        return self.project_service.get_current_project()

    def load_all_sessions_from_storage(self) -> List[Dict]:
        """从存储加载所有历史会话"""
        from storage.session_storage import get_session_storage
        storage = get_session_storage()

        # 从文件加载所有会话
        sessions = storage.load_all_sessions()

        if sessions:
            # 将会话添加到服务中
            self.session_service.sessions = sessions
            # 设置最后一个活动的会话为当前会话
            if sessions:
                self.session_service.current_session_id = sessions[0]["id"]
            logger.info(f"从存储加载了 {len(sessions)} 个历史会话")

        return sessions

    def switch_project(self, project_path: str) -> bool:
        """切换项目"""
        success = self.project_service.set_current_project(project_path)
        if success:
            logger.info(f"切换到项目：{Path(project_path).name}")
        return success

    def get_project_files(self, project_path: str) -> List[str]:
        """获取项目文件列表"""
        files = []
        exclude_dirs = {".git", "__pycache__", "node_modules",
                        ".venv", "venv", ".idea", ".vscode"}
        exclude_exts = {".pyc", ".pyo", ".so", ".dll", ".exe"}

        try:
            root_path = Path(project_path)
            for path in root_path.rglob("*"):
                if path.is_file():
                    # 检查是否在排除目录中
                    parts = path.relative_to(root_path).parts
                    if any(part in exclude_dirs for part in parts):
                        continue
                    # 检查扩展名
                    if path.suffix in exclude_exts:
                        continue
                    # 使用相对路径
                    rel_path = str(path.relative_to(root_path))
                    files.append(rel_path)

                    # 限制最大文件数
                    if len(files) >= 500:
                        break
        except Exception as e:
            logger.error(f"获取项目文件失败：{e}")

        return sorted(files)

    def handle_quick_command(self, content: str) -> Optional[Dict]:
        """
        处理快捷命令

        Returns:
            命令执行结果（如果有），None 表示不是快捷命令
        """
        cmd = content.lower().strip()

        if cmd == "/help":
            return {
                "type": "help",
                "content": self._get_help_text()
            }
        elif cmd == "/skills":
            return {
                "type": "skills",
                "content": self._get_skills_text()
            }
        elif cmd == "/rules":
            return {
                "type": "rules",
                "content": self._get_rules_text()
            }
        elif cmd == "/plan pause":
            return self._handle_plan_pause()
        elif cmd == "/plan resume":
            return self._handle_plan_resume()
        elif cmd == "/plan stop":
            return self._handle_plan_stop()
        elif cmd == "/plan status":
            return self._handle_plan_status()
        elif cmd == "/plan list":
            return self._handle_plan_list()

        return None

    def _handle_plan_pause(self) -> Dict:
        """处理计划暂停命令"""
        success = self.pause_current_plan()
        if success:
            return {"type": "plan_control", "content": "⏸️ 计划已暂停"}
        else:
            return {"type": "plan_control", "content": "⚠️ 没有可暂停的计划"}

    def _handle_plan_resume(self) -> Dict:
        """处理计划恢复命令"""
        success = self.resume_current_plan()
        if success:
            return {"type": "plan_control", "content": "▶️ 计划已恢复"}
        else:
            return {"type": "plan_control", "content": "⚠️ 没有可恢复的计划"}

    def _handle_plan_stop(self) -> Dict:
        """处理计划停止命令"""
        self.request_stop()
        return {"type": "plan_control", "content": "⏹️ 计划已停止"}

    def _handle_plan_status(self) -> Dict:
        """处理计划状态查询命令"""
        status = self.get_current_plan_status()
        if status:
            progress = status.get('progress', {})
            content = f"""📊 **计划状态**

- 计划名称：{status.get('name')}
- 状态：{status.get('status')}
- 进度：{progress.get('completed', 0)}/{progress.get('total', 0)} ({progress.get('percentage', 0):.1f}%)
- 当前步骤：{status.get('current_step', 0) + 1}/{status.get('total_steps', 0)}
"""
            return {"type": "plan_control", "content": content}
        else:
            return {"type": "plan_control", "content": "⚠️ 没有正在执行的计划"}

    def _handle_plan_list(self) -> Dict:
        """处理计划列表查询命令"""
        plans = self.list_active_plans()
        if plans:
            lines = ["📋 **活跃计划列表**\n"]
            for p in plans:
                progress = p.get('progress', {})
                lines.append(
                    f"- {p.get('name')} ({p.get('status')}) - {progress.get('percentage', 0):.1f}%")
            return {"type": "plan_control", "content": "\n".join(lines)}
        else:
            return {"type": "plan_control", "content": "📋 没有活跃的计划"}

    def _get_help_text(self) -> str:
        """获取帮助文本"""
        return """## 帮助信息

### 快捷命令
- `/help` - 显示此帮助信息
- `/skills` - 显示所有可用技能
- `/rules` - 显示所有已启用规则

### 功能入口
- **技能** - 管理和查看技能
- **项目** - 管理工作项目
- **规则** - 管理 AI 规则
- **模型** - 配置大语言模型

### 使用说明
直接输入问题或任务，AI 会智能分析并调用工具帮助完成。"""

    def _get_skills_text(self) -> str:
        """获取技能列表文本"""
        try:
            from core.skill_registry import get_skill_registry
            registry = get_skill_registry()
            skills = registry.list_skills()

            if skills:
                # 按级别分组
                builtin = [s for s in skills if s.level == "builtin"]
                global_skills = [s for s in skills if s.level == "global"]
                project_skills = [s for s in skills if s.level == "project"]

                lines = ["## 可用技能\n"]

                if builtin:
                    lines.append("### 内置技能")
                    for s in builtin:
                        lines.append(
                            f"- **{s.metadata.name}** - {s.metadata.description}")
                    lines.append("")

                if global_skills:
                    lines.append("### 全局技能")
                    for s in global_skills:
                        lines.append(
                            f"- **{s.metadata.name}** - {s.metadata.description}")
                    lines.append("")

                if project_skills:
                    lines.append("### 项目技能")
                    for s in project_skills:
                        lines.append(
                            f"- **{s.metadata.name}** - {s.metadata.description}")
                    lines.append("")

                lines.append("\n**💡 提示：** 点击标题栏「技能」可管理技能")
                return "\n".join(lines)
            else:
                return "暂无可用技能\n\n**💡 提示：** 点击标题栏「技能」可添加新技能"
        except Exception as e:
            return f"获取技能列表失败：{e}"

    def _get_rules_text(self) -> str:
        """获取规则列表文本"""
        try:
            from utils.rules_manager import get_rules_manager

            project_path = self.project_service.get_current_project()
            global_rules_dir = self._config.get_global_rules_path()
            rules_manager = get_rules_manager(
                project_path, global_rules_dir=global_rules_dir)
            rules = rules_manager.list_rules()

            # 只显示已启用的规则
            enabled_rules = [r for r in rules if r.enabled]

            if enabled_rules:
                # 按级别分组
                builtin = [r for r in enabled_rules if r.level == "builtin"]
                global_rules = [
                    r for r in enabled_rules if r.level == "global"]
                project_rules = [
                    r for r in enabled_rules if r.level == "project"]

                lines = ["## 已启用规则\n"]

                if builtin:
                    lines.append("### 内置规则")
                    for r in builtin:
                        lines.append(
                            f"- **{r.name}** - {r.description or '无描述'}")
                    lines.append("")

                if global_rules:
                    lines.append("### 全局规则")
                    for r in global_rules:
                        lines.append(
                            f"- **{r.name}** - {r.description or '无描述'}")
                    lines.append("")

                if project_rules:
                    lines.append("### 项目规则")
                    for r in project_rules:
                        lines.append(
                            f"- **{r.name}** - {r.description or '无描述'}")
                    lines.append("")

                lines.append("\n**💡 提示：** 点击标题栏「规则」可管理规则")
                return "\n".join(lines)
            else:
                return "暂无已启用规则\n\n**💡 提示：** 点击标题栏「规则」可添加新规则"
        except Exception as e:
            return f"获取规则列表失败：{e}"
