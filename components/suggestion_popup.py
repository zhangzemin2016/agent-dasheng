"""
智能提示浮层组件
支持指令提示和文件选择
"""

from typing import Callable, List, Dict, Any, Optional
import flet as ft

from theme import THEME


class SuggestionPopup(ft.Container):
    """智能提示浮层组件（使用 overlay 确保最上层显示）"""

    def __init__(self, on_select: Callable[[Any, str], None]):
        super().__init__()
        self.on_select = on_select
        self.items: List[Any] = []
        self.item_type: str = ""  # "command" or "file"
        self.selected_index: int = 0
        self._page: Optional[ft.Page] = None
        self._is_in_overlay = False

        # 建议列表
        self.list_view = ft.ListView(
            spacing=0,
            padding=ft.Padding.symmetric(vertical=4),
            auto_scroll=True
        )

        # 容器样式
        self.content = self.list_view
        self.bgcolor = THEME["sidebar_bg"]
        self.border = ft.Border.all(1, THEME["border_color"])
        self.border_radius = 8
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK)
        )
        self.visible = False
        self.bottom = 90  # 定位在输入框上方
        self.left = 280  # 侧边栏宽度
        self.right = 20
        self.height = 220

    def attach_page(self, page: ft.Page):
        """绑定页面引用"""
        self._page = page

    def show(self, items: List[Any], item_type: str):
        """显示建议列表"""
        if not items:
            self.hide()
            return

        self.items = items
        self.item_type = item_type
        self.selected_index = 0
        self._render_items()
        self.visible = True

        # 添加到 overlay 确保最上层显示
        if self._page and not self._is_in_overlay:
            self._page.overlay.append(self)
            self._is_in_overlay = True

    def hide(self):
        """隐藏浮层"""
        self.visible = False
        self.items = []
        self.selected_index = 0

        # 从 overlay 移除
        if self._page and self._is_in_overlay:
            try:
                self._page.overlay.remove(self)
            except ValueError:
                pass
            self._is_in_overlay = False

    def _render_items(self):
        """渲染列表项"""
        self.list_view.controls.clear()

        for i, item in enumerate(self.items):
            is_selected = i == self.selected_index

            if self.item_type == "command":
                # 指令项
                content = ft.Row([
                    ft.Icon(
                        ft.Icons.TERMINAL,
                        size=16,
                        color=THEME["accent_color"] if is_selected else THEME["secondary_text"]
                    ),
                    ft.Text(
                        item["cmd"],
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=THEME["text_color"]
                    ),
                    ft.Text(
                        item["desc"],
                        size=12,
                        color=THEME["secondary_text"]
                    )
                ], spacing=12)
            else:
                # 文件项
                # 根据文件类型选择图标
                icon = ft.Icons.INSERT_DRIVE_FILE
                if item.endswith(".py"):
                    icon = ft.Icons.CODE
                elif item.endswith(".md"):
                    icon = ft.Icons.DESCRIPTION
                elif item.endswith(".json") or item.endswith(".yaml") or item.endswith(".yml"):
                    icon = ft.Icons.SETTINGS
                elif "/" in item or "\\" in item:
                    parts = item.replace("\\", "/").split("/")
                    if len(parts) > 1:
                        icon = ft.Icons.FOLDER_OPEN

                content = ft.Row([
                    ft.Icon(
                        icon,
                        size=16,
                        color=THEME["accent_color"] if is_selected else THEME["secondary_text"]
                    ),
                    ft.Text(
                        item,
                        size=13,
                        color=THEME["text_color"],
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                ], spacing=8)

            item_container = ft.Container(
                content=content,
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                bgcolor=THEME["selected_bg"] if is_selected else None,
                border_radius=4,
                on_click=lambda e, idx=i: self._on_item_click(idx)
            )
            self.list_view.controls.append(item_container)

    def _on_item_click(self, index: int):
        """点击项目"""
        if 0 <= index < len(self.items):
            item = self.items[index]
            self.on_select(item, self.item_type)
            self.hide()

    def move_selection(self, direction: int):
        """移动选择（上下键）"""
        if not self.items:
            return

        self.selected_index += direction
        if self.selected_index < 0:
            self.selected_index = len(self.items) - 1
        elif self.selected_index >= len(self.items):
            self.selected_index = 0

        self._render_items()

    def confirm_selection(self):
        """确认选择（回车）"""
        if self.items and 0 <= self.selected_index < len(self.items):
            item = self.items[self.selected_index]
            self.on_select(item, self.item_type)
            self.hide()
            return True
        return False

    @property
    def is_visible(self) -> bool:
        """是否可见"""
        return self.visible
