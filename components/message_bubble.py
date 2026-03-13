"""
消息气泡组件
"""

import asyncio
import flet as ft
from theme import THEME
from .markdown_viewer import MarkdownViewer


class ThinkingIndicator(ft.Row):
    """思考中动画指示器 - 三个点上下跳动"""

    def __init__(self):
        self.dots = [
            ft.Container(
                width=6,
                height=6,
                border_radius=3,
                bgcolor=THEME["accent_color"],
                offset=ft.Offset(0, 0),
                animate_offset=ft.Animation(
                    300, ft.AnimationCurve.EASE_IN_OUT),
            )
            for _ in range(3)
        ]
        self._animating = False

        super().__init__(
            controls=self.dots,
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
        )

    def did_mount(self):
        self._animating = True
        self.page.run_task(self._animate)

    def will_unmount(self):
        self._animating = False

    async def _animate(self):
        while self._animating:
            for dot in self.dots:
                if not self._animating:
                    break
                # 向上跳
                dot.offset = ft.Offset(0, -1)
                try:
                    self.update()
                except Exception:
                    return
                await asyncio.sleep(0.15)
                # 落下
                dot.offset = ft.Offset(0, 0)
                try:
                    self.update()
                except Exception:
                    return
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.3)


class MessageBubble(ft.Container):
    """消息气泡组件 - 显示单条聊天消息（优化版）"""

    def __init__(self, role: str, content: str, thinking: bool = False):
        super().__init__()
        self.role = role
        self._is_thinking = thinking and role != "user"
        self._first_chunk = True
        self._is_streaming = False  # 是否正在流式输出

        # 根据角色设置样式
        bg_color = THEME["user_msg_bg"] if role == "user" else THEME["ai_msg_bg"]
        avatar_text = "你" if role == "user" else "AI"

        # 优化的配色方案
        # AI 头像使用深灰色
        avatar_bg = THEME["accent_color"] if role == "user" else "#4A4B5A"
        avatar_fg = "white" if role == "user" else "#ECECF1"  # AI 头像文字稍暗

        # 用户消息使用纯白色文字提升对比度，AI 消息使用主题文字色
        text_color = "#FFFFFF" if role == "user" else THEME["text_color"]

        # 头像（现代圆形设计）
        self.avatar = ft.Container(
            content=ft.Text(
                avatar_text,
                size=10,
                weight=ft.FontWeight.W_700,
                color=avatar_fg
            ),
            width=28,  # 稍微增大头像提升质感
            height=28,
            bgcolor=avatar_bg,
            border_radius=14,  # 完美圆形
            alignment=ft.Alignment.CENTER,
            margin=ft.Margin.only(right=10),  # 增加右边距
            shadow=ft.BoxShadow(  # 添加轻微阴影
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 2),
            ),
        )

        # 思考中指示器（精致版）
        self.thinking_indicator = ThinkingIndicator()
        # 思考指示器容器（用于控制显示/隐藏）
        self.thinking_container = ft.Container(
            content=self.thinking_indicator,
            visible=self._is_thinking,
            padding=ft.Padding.only(top=8),
        )

        # 消息内容：AI 消息使用 Markdown 渲染，用户消息使用纯文本
        if role == "user":
            self.content_text = ft.Text(
                content,
                size=14,
                color=text_color,
                selectable=True,
            )
        else:
            self.content_text = MarkdownViewer(
                value=content,
                selectable=True,
            )

        # 内容文本容器（初始时如果是思考状态则隐藏）
        self.content_text_container = ft.Container(
            content=self.content_text,
            visible=not self._is_thinking,
        )

        # 内容区域：使用 Column 同时容纳内容和思考指示器
        self.content_column = ft.Column(
            controls=[self.content_text_container, self.thinking_container],
            spacing=0,
            expand=True,
        )

        # 消息内容容器（带圆角和边距）
        self.content_wrapper = ft.Container(
            content=self.content_column,
            expand=True,
            padding=ft.Padding.symmetric(vertical=4, horizontal=8),
        )

        # 布局：优化间距和视觉层次
        # 用户消息靠右对齐，AI 消息靠左对齐
        if role == "user":
            self.content = ft.Row(
                controls=[
                    ft.Container(expand=True),  # 左侧占位，把内容挤到右边
                    ft.Row(
                        controls=[self.content_wrapper, self.avatar],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        else:
            self.content = ft.Row([
                self.avatar,
                self.content_wrapper,
            ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.START)

        # 背景色和边框
        self.bgcolor = bg_color
        # 为 AI 消息添加细微的左边框增强层次
        if role == "assistant" and bg_color == "transparent":
            self.border = ft.Border(
                left=ft.BorderSide(width=3, color=THEME["accent_color"])
            )
            self.padding = ft.Padding.symmetric(vertical=10, horizontal=14)
            self.border_radius = ft.BorderRadius.only(
                top_right=12, bottom_right=12, bottom_left=4
            )
        elif role == "user":
            # 用户消息圆角在左侧
            self.border_radius = ft.BorderRadius.only(
                top_left=12, bottom_left=12, bottom_right=4
            )
            self.padding = ft.Padding.symmetric(vertical=10, horizontal=14)
        else:
            self.padding = ft.Padding.symmetric(vertical=10, horizontal=14)

        self.expand = True
        # 添加悬停效果
        self.on_hover = self._on_hover

        # 添加淡入动画
        self.opacity = 0
        self.animate_opacity = ft.Animation(300, ft.AnimationCurve.EASE_OUT)

    def did_mount(self):
        """组件挂载时执行淡入动画"""
        self.opacity = 1
        try:
            self.update()
        except Exception:
            pass

    def _on_hover(self, e):
        """悬停效果"""
        if e.data == "true":
            self.bgcolor = THEME["hover_bg"] if self.role == "assistant" else "#454658"
        else:
            self.bgcolor = THEME["user_msg_bg"] if self.role == "user" else THEME["ai_msg_bg"]
        try:
            self.update()
        except Exception:
            pass

    def stop_thinking(self):
        """停止思考状态，隐藏思考动画"""
        if self._is_thinking or self._is_streaming:
            self._is_thinking = False
            self._is_streaming = False
            self._first_chunk = False
            # 隐藏思考指示器，显示内容
            self.thinking_container.visible = False
            self.content_text_container.visible = True
            try:
                self.update()
            except Exception:
                pass

    def mark_complete(self):
        """标记消息完成，隐藏思考动画"""
        self.stop_thinking()

    def append_text(self, text: str):
        """追加文本（用于流式输出）"""
        # 收到第一个 chunk 时，显示内容但保留思考动画
        if self._first_chunk:
            self._first_chunk = False
            self._is_streaming = True
            # 同时显示内容和思考动画
            self.content_text_container.visible = True
            self.thinking_container.visible = True
            self._is_thinking = False  # 不再是纯思考状态
            try:
                self.update()
            except Exception:
                pass

        if isinstance(self.content_text, MarkdownViewer):
            self.content_text.append_value(text)
        else:
            self.content_text.value += text
            try:
                self.update()
            except Exception:
                pass
