"""
状态指示器组件
提供清晰的操作状态反馈
"""

import flet as ft
from theme import THEME


class StatusIndicator(ft.Container):
    """状态指示器"""

    # 状态类型定义
    STATUS_THINKING = "thinking"
    STATUS_TOOL = "tool"
    STATUS_LOADING = "loading"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_CANCELLED = "cancelled"

    def __init__(self):
        super().__init__()
        self.visible = False
        self.padding = ft.Padding.all(8)
        self.border_radius = 6
        self.bgcolor = THEME["hover_bg"]

        # 状态图标和文本
        self.icon_map = {
            self.STATUS_THINKING: ft.Icons.PSychOLOGY_OUTLINED,
            self.STATUS_TOOL: ft.Icons.BUILD_OUTLINED,
            self.STATUS_LOADING: ft.Icons.HOURGLASS_EMPTY,
            self.STATUS_SUCCESS: ft.Icons.CHECK_CIRCLE_OUTLINE,
            self.STATUS_ERROR: ft.Icons.ERROR_OUTLINE,
            self.STATUS_CANCELLED: ft.Icons.CANCEL_OUTLINED,
        }

        # 状态颜色
        self.color_map = {
            self.STATUS_THINKING: "#9C8EFF",
            self.STATUS_TOOL: "#FFB74D",
            self.STATUS_LOADING: "#64B5F6",
            self.STATUS_SUCCESS: "#19C37D",
            self.STATUS_ERROR: "#C75450",
            self.STATUS_CANCELLED: "#A0A0A0",
        }

        # 内容
        self.status_icon = ft.Icon(size=16)
        self.status_text = ft.Text(size=12, color=THEME["secondary_text"])

        self.content = ft.Row([
            self.status_icon,
            self.status_text,
        ], spacing=6)

    def show(self, status_type: str, message: str = ""):
        """显示状态"""
        if status_type not in self.icon_map:
            raise ValueError(f"未知的状态类型：{status_type}")

        # 设置图标
        self.status_icon.name = self.icon_map[status_type]
        self.status_icon.color = self.color_map[status_type]

        # 设置文本
        if message:
            self.status_text.value = message
        else:
            self.status_text.value = self._get_default_message(status_type)

        self.visible = True

    def hide(self):
        """隐藏状态"""
        self.visible = False

    def _get_default_message(self, status_type: str) -> str:
        """获取默认状态文本"""
        messages = {
            self.STATUS_THINKING: "正在思考...",
            self.STATUS_TOOL: "正在执行工具...",
            self.STATUS_LOADING: "加载中...",
            self.STATUS_SUCCESS: "完成",
            self.STATUS_ERROR: "出错了",
            self.STATUS_CANCELLED: "已取消",
        }
        return messages.get(status_type, "")


class ToolCallIndicator(ft.Column):
    """工具调用指示器 - 显示工具调用的详细信息"""

    def __init__(self):
        super().__init__(spacing=4)
        self.visible = False

        # 工具名称
        self.tool_name = ft.Text(
            "",
            size=12,
            weight=ft.FontWeight.W_600,
            color=THEME["accent_color"]
        )

        # 工具参数
        self.tool_params = ft.Text("", size=11, color=THEME["secondary_text"])

        # 执行状态
        self.status_text = ft.Text("", size=11, italic=True)

        self.controls = [
            ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, size=14,
                        color=THEME["accent_color"]),
                self.tool_name
            ], spacing=4),
            self.tool_params,
            self.status_text,
        ]

    def show_call(self, tool_name: str, params: dict = None):
        """显示工具调用开始"""
        self.tool_name.value = f"调用工具：{tool_name}"
        self.tool_params.value = ""

        if params:
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            if len(param_str) > 80:
                param_str = param_str[:77] + "..."
            self.tool_params.value = f"参数：{param_str}"

        self.status_text.value = "准备执行..."
        self.status_text.color = THEME["secondary_text"]
        self.visible = True

    def show_executing(self):
        """显示执行中"""
        self.status_text.value = "正在执行..."
        self.status_text.color = THEME["accent_color"]

    def show_complete(self, result_preview: str = ""):
        """显示执行完成"""
        self.status_text.value = "✅ 执行完成"
        self.status_text.color = THEME["accent_color"]

        if result_preview:
            if len(result_preview) > 100:
                result_preview = result_preview[:97] + "..."
            self.tool_params.value = f"结果：{result_preview}"

    def show_error(self, error_message: str):
        """显示执行失败"""
        self.status_text.value = f"❌ 错误：{error_message}"
        self.status_text.color = "#C75450"

    def hide(self):
        """隐藏指示器"""
        self.visible = False
