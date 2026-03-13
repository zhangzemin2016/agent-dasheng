"""
AI Agent - Flet 桌面应用
基于 Flutter 的精美 UI

重构版本：使用 MVC 架构
"""

from utils.logger import get_logger
from components import MessageBubble, Sidebar, SuggestionPopup
from views import (
    ChatView,
    ProjectManagerView,
    RulesManagerView,
    show_model_config_dialog,
    SkillManagerView,
)
from controllers import MainController
from theme import THEME
import sys
import asyncio
from pathlib import Path
from typing import Optional

import flet as ft

# 添加路径以便导入
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


logger = get_logger("flet_app")


def show_snack_bar(page: ft.Page, message: str, duration: int = 3000):
    """显示 SnackBar"""
    try:
        snack = ft.SnackBar(content=ft.Text(message), duration=duration)
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        logger.error(f"显示 SnackBar 失败：{e}")


class AIAgentApp:
    """AI Agent 主应用类（精简版）"""

    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.controller: Optional[MainController] = None
        self.chat_view: Optional[ChatView] = None
        self.sidebar: Optional[Sidebar] = None
        self.suggestion_popup: Optional[SuggestionPopup] = None
        self.input_field: Optional[ft.TextField] = None
        self.send_btn: Optional[ft.IconButton] = None
        self.stop_btn: Optional[ft.IconButton] = None
        self.content_container: Optional[ft.Container] = None

    def init(self, page: ft.Page):
        """初始化应用"""
        self.page = page

        # 页面基础配置
        page.title = "AI Agent"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = THEME["bg_color"]
        page.padding = 0
        page.spacing = 0

        # 创建控制器
        self.controller = MainController(page)
        self.controller.init()

        # 构建 UI
        self._build_ui()

        # 加载项目列表
        self._load_projects()

        # 更新侧边栏会话列表
        self.sidebar.update_sessions(
            self.controller.get_all_sessions(),
            self.controller.session_service.current_session_id
        )

        # 加载当前会话的历史消息
        messages = self.controller.load_current_messages()
        if messages:
            self.chat_view.load_messages(messages)

        # 添加键盘事件监听
        page.on_keyboard_event = self._on_keyboard_event

        logger.info("应用初始化完成")

    def _build_ui(self):
        """构建用户界面"""
        # 侧边栏
        self.sidebar = Sidebar(
            on_new_chat=self._on_new_chat,
            on_session_select=self._on_session_select,
            on_session_delete=self._on_session_delete,
            on_project_change=self._on_project_change
        )

        # 聊天视图
        self.chat_view = ChatView()

        # 智能提示浮层
        self.suggestion_popup = SuggestionPopup(
            on_select=self._on_suggestion_select)
        self.suggestion_popup.attach_page(self.page)

        # 输入框
        self.input_field = ft.TextField(
            hint_text="输入消息，/ 命令，@ 选择文件...",
            multiline=True,
            shift_enter=True,
            min_lines=1,
            max_lines=5,
            border_radius=12,
            border_color=THEME["border_color"],
            focused_border_color=THEME["accent_color"],
            bgcolor=THEME["input_bg"],
            color=THEME["text_color"],
            expand=True,
            on_submit=self._on_send,
            on_change=self._on_input_change,
        )

        # 发送按钮
        self.send_btn = ft.IconButton(
            icon=ft.Icons.SEND, icon_color=THEME["accent_color"], on_click=self._on_send)

        # 停止按钮（生成时显示）
        self.stop_btn = ft.IconButton(
            icon=ft.Icons.STOP, icon_color="#C75450", on_click=self._on_stop,
            tooltip="停止执行",
            visible=False)

        # 输入区域（优化背景色）
        input_area = ft.Container(
            content=ft.Column([
                ft.Row([self.input_field, self.send_btn,
                       self.stop_btn], spacing=8),
                ft.Text("Enter 发送，Shift+Enter 换行，/ 命令，@ 文件",
                        size=11, color=THEME["secondary_text"]),
            ], spacing=4),
            padding=ft.Padding.all(16),
            bgcolor=THEME["bg_color"],
            border=ft.Border(top=ft.BorderSide(
                1, THEME["divider_color"])),  # 使用更柔和的分隔线
        )

        # 主内容区
        main_content = ft.Column([self.chat_view, ft.Container(
            content=input_area, expand=False)], spacing=0, expand=True)

        # 内容区域容器
        self.content_container = ft.Container(
            content=main_content, expand=True)

        # 整体布局（优化侧边栏分隔线）
        self.page.add(ft.Row([
            self.sidebar,
            ft.VerticalDivider(
                width=1, color=THEME["divider_color"]),  # 使用更柔和的分隔线
            self.content_container
        ], spacing=0, expand=True))

    def _load_projects(self):
        """加载项目列表"""
        projects = self.controller.project_service.get_all_projects()
        current_path = self.controller.get_current_project()
        self.sidebar.update_projects(projects, current_path)
        self.page.update()

    def _on_new_chat(self):
        """新建对话"""
        # 先保存当前会话（如果有）
        current_session = self.controller.session_service.get_current_session()
        if current_session and current_session.get("messages"):
            self.controller.save_current_session_with_summary()

        session = self.controller.create_new_session()
        self.chat_view.messages_column.controls.clear()
        self.sidebar.update_sessions(
            self.controller.get_all_sessions(), session["id"])
        self.page.update()

    def _on_session_select(self, session_id: str):
        """选择会话"""
        if self.controller.switch_session(session_id):
            # 使用新的 load_messages 方法，自动恢复思考状态
            messages = self.controller.load_current_messages()
            self.chat_view.load_messages(messages)

            self.sidebar.update_sessions(
                self.controller.get_all_sessions(), session_id)
            self.page.update()

    def _on_session_delete(self, session_id: str):
        """删除会话"""
        if self.controller.delete_session(session_id):
            # 使用新的 load_messages 方法，自动恢复思考状态
            messages = self.controller.load_current_messages()
            self.chat_view.load_messages(messages)

            self.sidebar.update_sessions(self.controller.get_all_sessions(
            ), self.controller.session_service.current_session_id)
            self.page.update()
        else:
            show_snack_bar(self.page, "无法删除最后一个对话")

    def _on_project_change(self, project_path: str):
        """切换项目"""
        if self.controller.switch_project(project_path):
            self._load_projects()
            show_snack_bar(self.page, f"已切换到项目：{Path(project_path).name}")
        else:
            show_snack_bar(self.page, "切换项目失败")

    def _show_model_config(self):
        """显示模型配置对话框"""
        def on_save():
            # 重新初始化 Agent
            try:
                from agent import create_agent
                from core.config_manager import get_config_manager

                llm_config = get_config_manager().get_llm_settings()
                self.controller.agent = create_agent(
                    temperature=llm_config.get("temperature", 0.7))
                if self.controller.agent.is_ready:
                    show_snack_bar(self.page, "模型配置已更新")
                    logger.info("DeepAgent 已根据新配置重新初始化")
                else:
                    show_snack_bar(self.page, "Agent 初始化未完成，请检查配置")
            except Exception as e:
                logger.error(f"更新模型配置失败：{e}")
                show_snack_bar(self.page, f"更新失败：{e}")

        try:
            show_model_config_dialog(self.page, on_save=on_save)
        except Exception as e:
            logger.error(f"显示模型配置失败：{e}")
            show_snack_bar(self.page, f"打开配置失败：{e}")

    async def _on_send_async(self, content: str, ai_bubble: MessageBubble):
        """异步发送消息处理（流式响应）"""
        self.controller.is_generating = True

        def update_ui():
            if self.page:
                self.page.update()

        # 准备历史记录
        session = self.controller.session_service.get_current_session()
        session_id = session["id"] if session else "default"

        project_path = self.controller.get_current_project() or ""

        try:
            async for chunk in self.controller.agent.stream_chat(
                content,
                project_path,
                session_id
            ):
                if self.controller._stop_requested:
                    break

                # 追加文本到气泡
                self.chat_view.append_ai_text(chunk)

                # 更新会话中的消息
                current_messages = self.controller.session_service.get_current_session()[
                    "messages"]
                message_index = len(current_messages) - 1
                if message_index < len(current_messages):
                    current_messages[message_index]["content"] += chunk

                # 更新 UI
                update_ui()
                await asyncio.sleep(0.01)

            # 标记为完成
            if self.controller.session_service.get_current_session():
                current_messages = self.controller.session_service.get_current_session()[
                    "messages"]
                message_index = len(current_messages) - 1
                if message_index < len(current_messages):
                    current_messages[message_index]["completed"] = True

            # 隐藏思考动画
            if self.chat_view.current_ai_message:
                self.chat_view.current_ai_message.mark_complete()

            update_ui()

            # 保存会话并生成摘要
            self.controller.save_current_session_with_summary()

        except asyncio.CancelledError:
            logger.info("流式响应任务被取消")
            if self.chat_view.current_ai_message:
                self.chat_view.current_ai_message.mark_complete()
                self.chat_view.current_ai_message.append_text("\n[已中断]")
        except Exception as e:
            logger.error(f"消息处理失败：{e}")
            if self.chat_view.current_ai_message:
                self.chat_view.current_ai_message.mark_complete()
                self.chat_view.current_ai_message.append_text(f"\n[错误：{e}]")
                update_ui()
        finally:
            self.controller.is_generating = False
            if self.page:
                self.send_btn.visible = True
                self.stop_btn.visible = False
                self.page.update()

    def _on_input_change(self, e):
        """输入框内容变化时触发"""
        text = self.input_field.value or ""

        if text.startswith("/"):
            self._show_command_suggestions(text[1:].lower())
        elif "@" in text:
            import re
            match = re.search(r'@(\S*)$', text)
            if match:
                self._show_file_suggestions(match.group(1))
            else:
                self._hide_suggestions()
        else:
            self._hide_suggestions()

    def _on_keyboard_event(self, e: ft.KeyboardEvent):
        """键盘事件处理"""
        if not self.suggestion_popup.is_visible:
            return

        if e.key == "Arrow Down":
            self.suggestion_popup.move_selection(1)
            self.page.update()
        elif e.key == "Arrow Up":
            self.suggestion_popup.move_selection(-1)
            self.page.update()
        elif e.key == "Escape":
            self._hide_suggestions()
        elif e.key == "Enter":
            if self.suggestion_popup.confirm_selection():
                self.page.update()

    def _show_command_suggestions(self, filter_text: str):
        """显示指令提示"""
        QUICK_COMMANDS = [
            {"cmd": "/help", "desc": "显示帮助信息"},
            {"cmd": "/skills", "desc": "显示可用技能"},
            {"cmd": "/rules", "desc": "显示已启用规则"},
        ]
        filtered = [
            c for c in QUICK_COMMANDS if filter_text in c["cmd"].lower()]
        self.suggestion_popup.show(filtered, "command")
        self.page.update()

    def _show_file_suggestions(self, filter_text: str):
        """显示文件选择提示"""
        project_path = self.controller.get_current_project()
        if not project_path:
            self._hide_suggestions()
            return

        files = self.controller.get_project_files(project_path)

        if filter_text:
            import re
            try:
                pattern = re.compile(filter_text, re.IGNORECASE)
                files = [f for f in files if pattern.search(f)]
            except re.error:
                files = [f for f in files if filter_text.lower() in f.lower()]

        self.suggestion_popup.show(files[:15], "file")
        self.page.update()

    def _hide_suggestions(self):
        """隐藏提示浮层"""
        self.suggestion_popup.hide()
        self.page.update()

    def _on_suggestion_select(self, item, item_type: str):
        """选择提示项回调"""
        if item_type == "command":
            self.input_field.value = item["cmd"]
        elif item_type == "file":
            import re
            text = self.input_field.value or ""
            text = re.sub(r'@\S*$', f'@{item} ', text)
            self.input_field.value = text

        self.suggestion_popup.hide()
        self.page.update()
        self.input_field.focus()

    def _on_send(self, e):
        """发送消息"""
        if self.controller.is_generating:
            return

        if self.suggestion_popup.is_visible:
            if self.suggestion_popup.confirm_selection():
                self.page.update()
                return

        content = self.input_field.value.strip()
        if not content:
            return

        self._hide_suggestions()
        self.input_field.value = ""
        self.page.update()

        # 检查快捷命令
        cmd_result = self.controller.handle_quick_command(content)
        if cmd_result:
            self._handle_quick_command_response(cmd_result, content)
            return

        if not self.controller.agent:
            show_snack_bar(self.page, "Agent 未初始化")
            return

        # 1. 先保存用户消息到存储
        self.controller.session_service.add_message("user", content)

        # 2. 再添加到 UI 显示
        self.chat_view.add_user_message(content)

        # 3. 添加 AI 消息占位到存储
        self.controller.session_service.add_message("assistant", "")

        # 4. 添加 AI 消息到 UI（思考状态）
        self.chat_view.add_ai_message("", thinking=True)

        self.send_btn.visible = False
        self.stop_btn.visible = True

        self.page.update()

        # 6. 启动流式响应任务
        self.page.run_task(self._on_send_async, content, None)

    def _handle_quick_command_response(self, cmd_result: dict, original_content: str):
        """处理快捷命令响应"""
        # 添加原始用户消息
        self.chat_view.add_user_message(original_content)
        self.controller.session_service.add_message("user", original_content)

        # 添加 AI 回复
        self.chat_view.add_ai_message(cmd_result["content"])
        self.controller.session_service.add_message(
            "assistant", cmd_result["content"])
        self.page.update()

    def _on_stop(self, e):
        """停止生成"""
        self.controller.request_stop()

        if self.chat_view.current_ai_message:
            bubble = self.chat_view.current_ai_message
            # 停止思考状态，显示内容
            if hasattr(bubble, 'stop_thinking'):
                bubble.stop_thinking()
            # 添加中断标记
            bubble.append_text("\n[已中断]")

        self.send_btn.visible = True
        self.stop_btn.visible = False
        self.page.update()

    def _show_skill_manager(self):
        """显示技能管理视图"""
        try:
            self.content_container.content = SkillManagerView(
                on_close=self._show_chat_view)
            self.page.update()
        except Exception as e:
            logger.error(f"显示技能管理失败：{e}")

    def _show_project_manager(self):
        """显示项目管理视图"""
        try:
            self.content_container.content = ProjectManagerView(
                on_close=self._show_chat_view,
                on_project_changed=lambda p: self._on_project_change(p)
            )
            self.page.update()
        except Exception as e:
            logger.error(f"显示项目管理失败：{e}")

    def _show_rules_manager(self):
        """显示规则管理视图"""
        try:
            self.content_container.content = RulesManagerView(
                on_close=self._show_chat_view)
            self.page.update()
        except Exception as e:
            logger.error(f"显示规则管理失败：{e}")

    def _show_chat_view(self):
        """返回聊天视图"""
        chat_view = ChatView()
        messages = self.controller.get_current_messages()

        for msg in messages:
            if msg["role"] == "user":
                chat_view.add_user_message(msg["content"])
            else:
                chat_view.add_ai_message(msg["content"])

        self.chat_view = chat_view

        # 重建主内容区
        input_area = ft.Container(
            content=ft.Column([
                ft.Row([self.input_field, self.send_btn,
                       self.stop_btn], spacing=8),
                ft.Text("Enter 发送，Shift+Enter 换行，/ 命令，@ 文件",
                        size=11, color=THEME["secondary_text"]),
            ], spacing=4),
            padding=ft.Padding.all(16),
            bgcolor=THEME["bg_color"],
            border=ft.Border(top=ft.BorderSide(1, THEME["border_color"])),
        )

        main_content = ft.Column([self.chat_view, ft.Container(
            content=input_area, expand=False)], spacing=0, expand=True)
        self.content_container.content = main_content
        self.page.update()


def main(page: ft.Page):
    """Flet 应用入口"""
    page.window_width = 1400
    page.window_height = 900
    page.window_min_width = 800
    page.window_min_height = 600

    app = AIAgentApp()
    page.app_instance = app

    # 设置标题栏菜单
    page.appbar = ft.AppBar(
        title=ft.Text("AI Agent"),
        bgcolor=THEME["sidebar_bg"],
        actions=[
            ft.TextButton(content=ft.Text(
                "模型", color=THEME["accent_color"]), on_click=lambda e: app._show_model_config()),
            ft.TextButton(content=ft.Text(
                "项目", color=THEME["text_color"]), on_click=lambda e: app._show_project_manager()),
            ft.TextButton(content=ft.Text(
                "技能", color=THEME["text_color"]), on_click=lambda e: app._show_skill_manager()),
            ft.TextButton(content=ft.Text(
                "规则", color=THEME["text_color"]), on_click=lambda e: app._show_rules_manager()),
            ft.Container(width=16),
        ],
    )

    app.init(page)


if __name__ == "__main__":
    ft.run(main)
