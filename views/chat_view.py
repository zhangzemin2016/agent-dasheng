"""
聊天视图组件
"""

from typing import Optional, List, Dict
import flet as ft
from theme import THEME

from components.message_bubble import MessageBubble


class ChatView(ft.Column):
    """聊天视图 - 显示消息列表"""

    def __init__(self):
        super().__init__()
        self.messages: List[MessageBubble] = []
        self.current_ai_message: Optional[MessageBubble] = None

        # 消息列表容器（优化间距和滚动）
        self.messages_column = ft.Column(
            spacing=8,  # 增加消息间距提升层次感
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            auto_scroll=True,  # 自动滚动到底部
        )

        # 内容区域（带背景色）
        self.content_area = ft.Container(
            content=self.messages_column,
            expand=True,
            alignment=ft.Alignment.TOP_CENTER,
            bgcolor=THEME["chat_bg"],
        )

        self.controls = [self.content_area]
        self.expand = True
        self.spacing = 0

    def add_user_message(self, content: str):
        """添加用户消息"""
        bubble = MessageBubble("user", content)
        self.messages.append(bubble)
        self.messages_column.controls.append(bubble)
        self.current_ai_message = None
        # 立即更新 UI 确保消息显示
        try:
            self.update()
        except Exception:
            pass

    def add_ai_message(self, content: str = "", thinking: bool = False):
        """添加 AI 消息，返回消息气泡以便流式更新"""
        bubble = MessageBubble("assistant", content, thinking=thinking)
        self.messages.append(bubble)
        self.messages_column.controls.append(bubble)
        self.current_ai_message = bubble
        # 立即更新 UI 确保消息显示
        try:
            self.update()
        except Exception:
            pass
        return bubble

    def append_ai_text(self, text: str):
        """向当前 AI 消息追加文本"""
        if self.current_ai_message:
            self.current_ai_message.append_text(text)
            # 流式更新时不需要频繁调用 update()，由 append_text 内部处理

    def load_messages(self, messages: List[Dict]):
        """加载历史消息列表"""
        # 清空现有消息
        self.messages_column.controls.clear()
        self.messages.clear()
        self.current_ai_message = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            completed = msg.get("completed", True)  # 默认已完成

            # 如果是 AI 消息且未完成，显示思考状态
            thinking = (role == "assistant" and not completed)

            bubble = MessageBubble(role, content, thinking=thinking)
            self.messages.append(bubble)
            self.messages_column.controls.append(bubble)

            # 如果正在思考中，设置为当前消息
            if thinking:
                self.current_ai_message = bubble

        # 加载完成后更新 UI
        try:
            self.update()
        except Exception:
            pass
