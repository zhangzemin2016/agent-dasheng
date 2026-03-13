"""
通用 Markdown 渲染组件
"""

import flet as ft
from theme import THEME


class MarkdownViewer(ft.Markdown):
    """通用 Markdown 渲染组件（优化版）

    封装统一的 Markdown 渲染逻辑，支持代码高亮和 GitHub 风格扩展
    """

    def __init__(
        self,
        value: str = "",
        selectable: bool = True,
        on_tap_link=None,
        **kwargs
    ):
        super().__init__(
            value=value,
            selectable=selectable,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            code_theme=ft.MarkdownCodeTheme.MONOKAI,  # 使用 Monokai 深色主题
            on_tap_link=on_tap_link,
            **kwargs
        )

    def set_value(self, value: str):
        """设置 Markdown 内容"""
        self.value = value

    def append_value(self, text: str):
        """追加内容（用于流式输出）"""
        self.value = (self.value or "") + text
