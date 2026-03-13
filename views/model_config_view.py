"""
模型配置视图
配置 LLM 模型参数
"""

from typing import Callable, Optional
import flet as ft

from core.config_manager import get_config_manager
from theme import THEME

# 获取全局配置管理器实例
_config = get_config_manager()


class ModelConfigView(ft.Column):
    """模型配置视图"""

    def __init__(self, on_save: Callable = None, on_cancel: Callable = None):
        super().__init__()
        self.on_save = on_save
        self.on_cancel = on_cancel

        self.spacing = 0
        self.expand = True

        # 加载当前配置
        self.config = _config.get_llm_settings()
        self.providers_data = self.config.get("providers", {})
        self.builtin_providers = _config.get_builtin_providers()

        # 当前编辑的提供商
        self.current_provider_id: Optional[str] = None
        self.is_editing_custom = False

        # 提供商列表
        self.provider_list = ft.ListView(
            expand=1,
            spacing=4,
            padding=ft.Padding(0, 0, 8, 0),
        )

        # 更新提供商列表显示
        self._refresh_provider_list()

        # 提供商选择（下拉框）
        all_providers = _config.get_all_providers()
        current_provider = self.config.get("provider", "ollama")
        provider_options = [
            ft.DropdownOption(key=p, text=_config.get_provider_display_name(p))
            for p in all_providers
        ]
        self.provider_dropdown = ft.Dropdown(
            label="当前使用模型",
            value=current_provider,
            options=provider_options,
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            dense=True,
            on_select=self._on_provider_change,
            expand=True,
        )

        # 添加按钮
        self.add_btn = ft.IconButton(
            ft.Icons.ADD_CIRCLE_OUTLINED,
            tooltip="添加自定义模型",
            icon_color=THEME["accent_color"],
            on_click=self._on_add_provider,
        )

        # 编辑按钮
        self.edit_btn = ft.IconButton(
            ft.Icons.EDIT_OUTLINED,
            tooltip="编辑当前模型",
            icon_color=THEME["accent_color"],
            on_click=self._on_edit_provider,
            disabled=True,
        )

        # 删除按钮
        self.delete_btn = ft.IconButton(
            ft.Icons.DELETE_OUTLINE,
            tooltip="删除当前模型",
            icon_color=THEME["accent_color"],
            on_click=self._on_delete_provider,
            disabled=True,
        )

        # 温度参数
        self.temperature_slider = ft.Slider(
            value=self.config.get("temperature", 0.7),
            min=0,
            max=2,
            divisions=20,
            label="{value}",
            on_change=self._on_temperature_change
        )
        self.temperature_text = ft.Text(
            f"温度：{self.temperature_slider.value}",
            color=THEME["text_color"]
        )

        # 各提供商配置字段
        self.model_field = ft.TextField(
            label="模型名称",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            dense=True,
            read_only=True,
        )
        self.api_key_field = ft.TextField(
            label="API Key",
            password=True,
            can_reveal_password=True,
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            dense=True,
            read_only=True,
        )
        self.base_url_field = ft.TextField(
            label="Base URL",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            dense=True,
            read_only=True,
        )

        # 自定义字段（用于添加/编辑时）
        self.custom_id_field = ft.TextField(
            label="厂商标识符",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            dense=True,
            visible=False,
        )

        # 配置区域
        self.config_container = ft.Column(spacing=12)

        # 操作提示
        self.hint_text = ft.Text(
            "💡 点击 + 添加自定义模型，或选择模型后点击 ✏️ 编辑",
            size=12,
            color=THEME["text_color"],
            italic=True,
        )

        # 保存/取消按钮
        self.save_btn = ft.ElevatedButton(
            "保存",
            bgcolor=THEME["accent_color"],
            color=ft.Colors.WHITE,
            on_click=self._on_save
        )
        self.cancel_btn = ft.TextButton(
            "取消",
            on_click=self._on_cancel
        )

        self.controls = [
            ft.Container(
                content=ft.Row([
                    # 左侧：模型列表
                    ft.Container(
                        content=ft.Column([
                            ft.Text("模型列表", weight=ft.FontWeight.W_600, size=14),
                            ft.Container(
                                content=self.provider_list,
                                border=ft.border.all(1, THEME["border_color"]),
                                border_radius=5,
                                padding=5,
                                height=200,
                            ),
                        ], spacing=8),
                        width=180,
                        padding=ft.Padding(0, 0, 16, 0),
                    ),
                    # 右侧：配置区域
                    ft.Container(
                        content=ft.Column([
                            # 顶部：当前使用模型 + 操作按钮
                            ft.Row([
                                self.provider_dropdown,
                                self.add_btn,
                                self.edit_btn,
                                self.delete_btn,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            self.hint_text,
                            ft.Divider(height=1, color=THEME["border_color"]),
                            # 温度参数
                            ft.Column([
                                self.temperature_text,
                                self.temperature_slider
                            ], spacing=4),
                            # 详细配置
                            self.config_container,
                        ], spacing=12),
                        expand=True,
                    ),
                ], spacing=16),
                width=600,
                padding=ft.Padding.only(bottom=16)
            ),
            ft.Row([
                self.cancel_btn,
                self.save_btn
            ], alignment=ft.MainAxisAlignment.END, spacing=8)
        ]

        # 初始化配置字段（不调用 update）
        self._init_config_fields()

        # 初始化按钮状态
        self._update_button_state()

    def _refresh_provider_list(self):
        """刷新模型列表显示"""
        self.provider_list.controls.clear()
        all_providers = _config.get_all_providers()
        current = self.config.get("provider", "")

        for provider_id in all_providers:
            is_builtin = provider_id in self.builtin_providers
            is_current = provider_id == current
            display_name = get_provider_display_name(provider_id)

            # 创建列表项
            tile = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(
                            display_name, size=13, weight=ft.FontWeight.W_600 if is_current else None),
                        ft.Text(
                            "内置" if is_builtin else "自定义",
                            size=11,
                            color=THEME["text_color"],
                        ),
                    ], expand=True, spacing=2),
                ], spacing=8),
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=5,
                bgcolor=THEME["accent_color"] if is_current else None,
                on_click=lambda e, pid=provider_id: self._on_select_provider(
                    pid),
            )
            # 设置选中时的文字颜色
            if is_current:
                tile.content.controls[0].controls[0].color = ft.Colors.WHITE
                tile.content.controls[0].controls[1].color = ft.Colors.WHITE70
            self.provider_list.controls.append(tile)

    def _on_select_provider(self, provider_id: str):
        """选择模型提供商"""
        self.provider_dropdown.value = provider_id
        # 更新当前使用的提供商
        self.config["provider"] = provider_id
        self._update_button_state()
        self._update_config_fields()
        # 刷新列表高亮
        self._refresh_provider_list()

    def _update_button_state(self):
        """更新按钮状态"""
        provider_id = self.provider_dropdown.value
        is_builtin = provider_id in self.builtin_providers

        # 内置模型只能编辑，不能删除
        # 自定义模型可以编辑和删除
        self.edit_btn.disabled = False
        self.delete_btn.disabled = is_builtin

    def _init_config_fields(self):
        """初始化配置字段（不触发 update）"""
        # 重置编辑状态
        self.is_editing_custom = False
        self.current_provider_id = None

        provider = self.provider_dropdown.value
        provider_config = self.providers_data.get(provider, {})

        # 设置为只读模式
        self.model_field.read_only = True
        self.api_key_field.read_only = True
        self.base_url_field.read_only = True
        self.custom_id_field.visible = False

        self.config_container.controls.clear()

        # 模型名称
        self.model_field.value = provider_config.get("model", "")
        self.config_container.controls.append(self.model_field)

        # API Key (DeepSeek 和 OpenAI 需要)
        if provider in ["deepseek", "openai"] or "api_key" in provider_config:
            self.api_key_field.value = provider_config.get("api_key", "")
            self.config_container.controls.append(self.api_key_field)

        # Base URL (Ollama 需要)
        if provider == "ollama" or "base_url" in provider_config:
            self.base_url_field.value = provider_config.get(
                "base_url", "http://localhost:11434")
            self.config_container.controls.append(self.base_url_field)

    def _on_provider_change(self, e):
        """提供商变更"""
        self._update_button_state()
        self._update_config_fields()

    def _on_add_provider(self, e):
        """添加新的模型提供商"""
        # 获取所有已存在的提供商
        all_providers = _config.get_all_providers()

        # 进入编辑模式
        self.is_editing_custom = True
        self.current_provider_id = None

        # 显示自定义字段
        self.custom_id_field.visible = True
        self.custom_id_field.value = ""
        self.model_field.read_only = False
        self.api_key_field.read_only = False
        self.base_url_field.read_only = False

        # 清空配置区域，重新添加可编辑的字段
        self.config_container.controls.clear()
        self.config_container.controls.append(self.custom_id_field)
        self.config_container.controls.append(self.model_field)
        self.config_container.controls.append(self.api_key_field)
        # Base URL 字段暂时不添加，根据类型动态添加

        self.hint_text.value = "📝 正在添加新模型，请填写完整信息"
        self.update()

    def _on_edit_provider(self, e):
        """编辑当前模型提供商"""
        provider_id = self.provider_dropdown.value
        self.is_editing_custom = True
        self.current_provider_id = provider_id

        # 如果是内置模型，不允许修改标识符
        is_builtin = provider_id in self.builtin_providers
        self.custom_id_field.visible = not is_builtin
        self.custom_id_field.value = provider_id if not is_builtin else ""
        self.custom_id_field.read_only = is_builtin

        # 设置为可编辑
        self.model_field.read_only = False
        self.api_key_field.read_only = False
        self.base_url_field.read_only = False

        # 加载当前配置
        provider_config = self.providers_data.get(provider_id, {})
        self.model_field.value = provider_config.get("model", "")
        self.api_key_field.value = provider_config.get("api_key", "")
        self.base_url_field.value = provider_config.get("base_url", "")

        # 清空配置区域，重新添加可编辑的字段
        self.config_container.controls.clear()
        if not is_builtin:
            self.config_container.controls.append(self.custom_id_field)
        self.config_container.controls.append(self.model_field)
        self.config_container.controls.append(self.api_key_field)
        if provider_id == "ollama" or "base_url" in provider_config:
            self.config_container.controls.append(self.base_url_field)

        self.hint_text.value = f"📝 正在编辑模型：{_config.get_provider_display_name(provider_id)}"
        self.update()

    def _on_delete_provider(self, e):
        """删除当前模型提供商"""
        provider_id = self.provider_dropdown.value

        # 二次确认
        def confirm_delete(e):
            success = _config.remove_provider(provider_id)
            if success:
                # 重新加载配置
                self.config = _config.get_llm_settings()
                self.providers_data = self.config.get("providers", {})

                # 刷新列表和下拉框
                self._refresh_provider_list()
                self._refresh_dropdown_options()

                # 重置状态
                self.is_editing_custom = False
                self.current_provider_id = None

                # 初始化配置字段
                self._init_config_fields()
                self._update_button_state()

                self.hint_text.value = "💡 点击 + 添加自定义模型，或选择模型后点击 ✏️ 编辑"
                self.update()

            # 关闭对话框
            if self.page:
                self.page.close_dialog()

        # 显示确认对话框
        if self.page:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("确认删除"),
                    content=ft.Text(f"确定要删除模型 {provider_id} 吗？此操作不可恢复。"),
                    actions=[
                        ft.TextButton(
                            "取消", on_click=lambda e: self.page.close_dialog()),
                        ft.ElevatedButton(
                            "删除", on_click=confirm_delete, bgcolor=THEME["accent_color"], color=ft.Colors.WHITE),
                    ],
                )
            )

    def _on_temperature_change(self, e):
        """温度参数变更"""
        self.temperature_text.value = f"温度: {e.control.value:.1f}"
        self.update()

    def _update_config_fields(self):
        """更新配置字段"""
        # 如果不是编辑模式，设置为只读
        if not self.is_editing_custom:
            self.model_field.read_only = True
            self.api_key_field.read_only = True
            self.base_url_field.read_only = True
            self.custom_id_field.visible = False

            provider = self.provider_dropdown.value
            provider_config = self.providers_data.get(provider, {})

            self.config_container.controls.clear()

            # 模型名称
            self.model_field.value = provider_config.get("model", "")
            self.config_container.controls.append(self.model_field)

            # API Key (DeepSeek 和 OpenAI 需要)
            if provider in ["deepseek", "openai"] or "api_key" in provider_config:
                self.api_key_field.value = provider_config.get("api_key", "")
                self.config_container.controls.append(self.api_key_field)

            # Base URL (Ollama 需要)
            if provider == "ollama" or "base_url" in provider_config:
                self.base_url_field.value = provider_config.get(
                    "base_url", "http://localhost:11434")
                self.config_container.controls.append(self.base_url_field)

            self.hint_text.value = "💡 点击 + 添加自定义模型，或选择模型后点击 ✏️ 编辑"

        # 安全更新
        if self.page:
            self.update()

    def _refresh_dropdown_options(self):
        """刷新下拉框选项"""
        all_providers = _config.get_all_providers()
        current_provider = self.config.get("provider", "ollama")

        self.provider_dropdown.options = [
            ft.DropdownOption(key=p, text=_config.get_provider_display_name(p))
            for p in all_providers
        ]
        self.provider_dropdown.value = current_provider

    def _on_save(self, e):
        """保存配置"""
        # 如果是编辑模式
        if self.is_editing_custom:
            provider_id = self.custom_id_field.value if self.custom_id_field.visible else self.provider_dropdown.value

            # 验证必填字段
            if not provider_id:
                self._show_error("请填写厂商标识符")
                return

            if not self.model_field.value:
                self._show_error("请填写模型名称")
                return

            # 构建配置
            provider_config = {
                "model": self.model_field.value,
            }

            # 根据字段存在情况添加其他配置
            if self.api_key_field.visible and self.api_key_field.value:
                provider_config["api_key"] = self.api_key_field.value

            if self.base_url_field.visible and self.base_url_field.value:
                provider_config["base_url"] = self.base_url_field.value

            # 判断是添加还是更新
            if self.current_provider_id is None:
                # 添加新提供商
                success = _config.add_provider(provider_id, provider_config)
                if not success:
                    self._show_error(f"提供商 {provider_id} 已存在")
                    return
            else:
                # 更新现有提供商
                # 如果标识符改变了，需要先删除旧的再添加新的
                if provider_id != self.current_provider_id:
                    _config.remove_provider(self.current_provider_id)
                success = update_provider(provider_id, provider_config)
                if not success:
                    self._show_error(f"提供商 {provider_id} 不存在")
                    return

            # 重新加载配置
            self.config = _config.get_llm_settings()
            self.providers_data = self.config.get("providers", {})

            # 刷新 UI
            self._refresh_provider_list()
            self._refresh_dropdown_options()

            # 退出编辑模式
            self.is_editing_custom = False
            self.current_provider_id = None
            self.custom_id_field.visible = False
            self.model_field.read_only = True
            self.api_key_field.read_only = True
            self.base_url_field.read_only = True

            # 初始化配置字段
            self._init_config_fields()
            self._update_button_state()

            self.hint_text.value = "💡 点击 + 添加自定义模型，或选择模型后点击 ✏️ 编辑"
            self.update()

            # 通知保存成功
            if self.on_save:
                self.on_save()
        else:
            # 普通保存（只保存温度参数）
            provider = self.provider_dropdown.value

            # 构建新配置
            new_config = {
                "provider": provider,
                "temperature": self.temperature_slider.value,
                "providers": self.providers_data.copy()
            }

            # 保存
            save_llm_settings(new_config)

            # 更新全局变量
            global LLM_PROVIDER, LLM_CONFIG
            LLM_PROVIDER = provider
            LLM_CONFIG = new_config["providers"]

            if self.on_save:
                self.on_save()

    def _show_error(self, message: str):
        """显示错误提示"""
        if self.page:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("错误", color=ft.Colors.RED),
                    content=ft.Text(message),
                    actions=[
                        ft.ElevatedButton(
                            "确定", on_click=lambda e: self.page.close_dialog())
                    ],
                )
            )

    def _on_cancel(self, e):
        """取消"""
        if self.on_cancel:
            self.on_cancel()


def show_model_config_dialog(page: ft.Page, on_save: Callable = None):
    """显示模型配置对话框"""
    dialog = None

    def close_dialog():
        page.pop_dialog()

    view = ModelConfigView(
        on_save=lambda: (close_dialog(), on_save() if on_save else None),
        on_cancel=close_dialog
    )

    dialog = ft.AlertDialog(
        title=ft.Text("模型配置", size=18, weight=ft.FontWeight.W_600),
        content=view,
        actions=[],
        modal=True,
        inset_padding=20
    )

    page.show_dialog(dialog)
