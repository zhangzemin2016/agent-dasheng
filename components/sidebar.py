"""
侧边栏组件
"""

from typing import Optional, List, Dict, Callable
import flet as ft

from theme import THEME


class Sidebar(ft.Container):
    """侧边栏 - 显示会话列表和项目选择"""

    def __init__(
        self,
        on_new_chat: Callable,
        on_session_select: Callable,
        on_session_delete: Callable,
        on_project_change: Callable,
        on_skill_manager: Callable = None,
        on_project_manager: Callable = None,
        on_rules_manager: Callable = None,
        on_model_config: Callable = None
    ):
        super().__init__()
        self.on_new_chat = on_new_chat
        self.on_session_select = on_session_select
        self.on_session_delete = on_session_delete
        self.on_project_change = on_project_change
        self.on_skill_manager = on_skill_manager
        self.on_project_manager = on_project_manager
        self.on_rules_manager = on_rules_manager
        self.on_model_config = on_model_config

        self.sessions: List[Dict] = []
        self.current_session_id: Optional[str] = None
        self.current_project = "未选择项目"

        # 新建对话按钮（优化样式）
        self.new_chat_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=18,
                        color=THEME["accent_color"]),
                ft.Text("新建对话", size=14, weight=ft.FontWeight.W_600)
            ], spacing=8),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TRANSPARENT,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, THEME["border_color"]),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            ),
            on_click=lambda _: on_new_chat(),
        )

        # 会话列表（优化间距）
        self.session_list = ft.ListView(
            spacing=4,  # 增加间距提升层次感
            padding=ft.Padding.symmetric(horizontal=12),
            expand=True,
            auto_scroll=False,
        )

        # 项目下拉选择（优化样式）
        self.project_dropdown = ft.Dropdown(
            label="当前项目",
            value=self.current_project,
            options=[],
            border_color=THEME["border_color"],
            focused_border_color=THEME["accent_color"],
            filled=True,
            bgcolor=THEME["input_bg"],  # 与输入框背景统一
            color=THEME["text_color"],
            label_style=ft.TextStyle(color=THEME["secondary_text"]),
            expand=True,
            on_select=self._on_project_change,
        )

        # 侧边栏布局（优化分隔线）
        self.content = ft.Column([
            # 新建按钮
            ft.Container(
                content=self.new_chat_btn,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8)
            ),
            # 分隔线（使用更柔和的颜色）
            ft.Divider(color=THEME["divider_color"], height=1),
            # 历史对话标题
            ft.Container(
                content=ft.Text(
                    "历史对话",
                    size=12,
                    color=THEME["secondary_text"],
                    weight=ft.FontWeight.W_500
                ),
                padding=ft.Padding.only(left=16, top=12, bottom=8)
            ),
            # 会话列表
            self.session_list,

            # 底部项目选择
            ft.Container(
                content=ft.Column([
                    ft.Divider(color=THEME["divider_color"], height=1),
                    ft.Container(
                        content=self.project_dropdown,
                        padding=ft.Padding.all(12)
                    )
                ], spacing=0)
            ),
        ], spacing=0, expand=True)

        self.bgcolor = THEME["sidebar_bg"]
        self.width = 260
        self.expand = False

    def update_sessions(self, sessions: List[Dict], current_id: str):
        """更新会话列表"""
        self.sessions = sessions
        self.current_session_id = current_id
        self.session_list.controls.clear()

        # 至少保留一个会话，只有一个时隐藏删除按钮
        show_delete = len(sessions) > 1

        for session in sessions:
            is_selected = session["id"] == current_id

            # 会话项布局：标题 + 删除按钮
            row_controls = [
                ft.Container(
                    content=ft.Text(
                        session.get("title", "新对话"),
                        size=14,
                        color=THEME["text_color"],
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    expand=True,
                    on_click=lambda e, sid=session["id"]: self.on_session_select(
                        sid),
                ),
            ]

            # 只有多个会话时才显示删除按钮
            if show_delete:
                row_controls.append(
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        icon_color=THEME["secondary_text"],
                        tooltip="删除对话",
                        on_click=lambda e, sid=session["id"]: self._confirm_delete(
                            sid),
                    )
                )

            item = ft.Container(
                content=ft.Row(
                    row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(
                    left=16, top=8, bottom=8, right=4 if show_delete else 16),
                bgcolor=THEME["selected_bg"] if is_selected else None,
                border_radius=8,
                on_hover=lambda e: self._on_item_hover(e),
            )
            # 为选中项添加左边框指示器
            if is_selected:
                item.border = ft.Border(
                    left=ft.BorderSide(width=3, color=THEME["accent_color"])
                )
            self.session_list.controls.append(item)

    def _on_item_hover(self, e):
        """鼠标悬停效果"""
        if e.data == "true":
            e.control.bgcolor = THEME["hover_bg"]
        else:
            # 检查是否是当前选中项
            idx = self.session_list.controls.index(e.control)
            if idx < len(self.sessions) and self.sessions[idx]["id"] == self.current_session_id:
                e.control.bgcolor = THEME["selected_bg"]
            else:
                e.control.bgcolor = None
        e.control.update()

    def _confirm_delete(self, session_id: str):
        """确认删除对话"""
        self.on_session_delete(session_id)

    def update_projects(self, projects: List[Dict], current_path: str):
        """更新项目列表"""
        options = [
            ft.DropdownOption(
                key=p.get("path", ""),
                text=p.get("name", "未命名")
            )
            for p in projects
        ]
        self.project_dropdown.options = options

        for project in projects:
            if project.get("path") == current_path:
                self.current_project = project.get("name", "未命名")
                self.project_dropdown.value = current_path
                break

    def _on_project_change(self, e):
        """项目选择变更回调"""
        if e.control.value:
            self.on_project_change(e.control.value)
