"""
Rules 管理视图
支持项目路径 rules 目录下的多规则文件管理
"""

from typing import Callable
import flet as ft

from core.config_manager import get_config_manager
from utils.rules_manager import get_rules_manager, Rule
from theme import THEME
from components.markdown_viewer import MarkdownViewer

# 获取配置管理器实例
_config = get_config_manager()


def _show_snack_bar(page, message: str, duration: int = 3000):
    """显示 SnackBar"""
    try:
        snack = ft.SnackBar(content=ft.Text(message), duration=duration)
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception:
        pass


def handle_view_error(page, error: Exception, context: str = ""):
    """视图错误处理"""
    import traceback
    from utils.logger import get_logger
    logger = get_logger("rules_manager_view")

    error_msg = str(error)
    context_str = f" [{context}]" if context else ""
    logger.error(f"错误{context_str}: {error_msg}\n{traceback.format_exc()}")
    _show_snack_bar(page, f"错误{context_str}: {error_msg}", duration=5000)


class RulesManagerView(ft.Column):
    """Rules 管理视图"""

    def __init__(self, on_close: Callable = None):
        super().__init__()
        self.on_close = on_close

        self.spacing = 0
        self.expand = True

        # 获取当前项目路径和全局规则目录
        project_path = _config.get_current_project_path()
        global_rules_dir = _config.get_global_rules_path()
        self.rules_manager = get_rules_manager(
            project_path, global_rules_dir=global_rules_dir)

        # 当前选中的规则
        self.current_rule: Rule = None
        # 编辑/预览模式
        self.is_preview_mode = False

        # 规则列表 - 按级别分组
        self.builtin_rules_list = ft.ListView(
            spacing=4, padding=ft.Padding.symmetric(horizontal=12))
        self.global_rules_list = ft.ListView(
            spacing=4, padding=ft.Padding.symmetric(horizontal=12))
        self.project_rules_list = ft.ListView(
            spacing=4, padding=ft.Padding.symmetric(horizontal=12))

        # 编辑器
        self.name_field = ft.TextField(
            label="规则名称",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            bgcolor=THEME["bg_color"]
        )
        self.desc_field = ft.TextField(
            label="描述",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            bgcolor=THEME["bg_color"]
        )
        self.priority_field = ft.TextField(
            label="优先级",
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            bgcolor=THEME["bg_color"],
            width=70
        )
        self.enabled_switch = ft.Switch(
            label="启用",
            value=True
        )
        self.content_editor = ft.TextField(
            label="规则内容 (Markdown)",
            multiline=True,
            min_lines=15,
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            bgcolor=THEME["bg_color"],
            expand=True
        )

        # Markdown 预览组件
        self.content_preview = MarkdownViewer(
            value="",
            selectable=True
        )
        self.preview_container = ft.Container(
            content=self.content_preview,
            expand=True,
            padding=ft.Padding.all(12),
            bgcolor=THEME["bg_color"],
            border=ft.Border.all(1, THEME["border_color"]),
            border_radius=4,
            visible=False  # 默认隐藏
        )

        # 编辑/预览切换按钮
        self.toggle_preview_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.PREVIEW, size=18),
                ft.Text("预览", size=14)
            ]),
            bgcolor=THEME["hover_bg"],
            color=THEME["text_color"],
            on_click=self._toggle_preview
        )

        # 规则目录提示
        rules_dir = self.rules_manager.get_rules_dir()
        dir_hint = ft.Container(
            content=ft.Text(
                f"规则目录: {rules_dir}" if rules_dir else "请先选择项目",
                size=11,
                color=THEME["secondary_text"]
            ),
            padding=ft.Padding.symmetric(horizontal=20, vertical=4)
        )

        # 标题栏
        header = ft.Container(
            content=ft.Row([
                ft.Text("Rules 管理", size=20,
                        weight=ft.FontWeight.W_600, color=THEME["text_color"]),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD, size=18),
                            ft.Text("新建", size=14)
                        ]),
                        bgcolor=THEME["accent_color"],
                        color=ft.Colors.WHITE,
                        on_click=self._on_new_rule
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE, size=18),
                            ft.Text("保存", size=14)
                        ]),
                        bgcolor=THEME["accent_color"],
                        color=ft.Colors.WHITE,
                        on_click=self._on_save
                    ),
                    self.toggle_preview_btn,
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=THEME["secondary_text"],
                        tooltip="关闭",
                        on_click=self._on_close
                    )
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding.all(20)
        )

        # 左侧规则列表区域 - 三级分组
        left_panel = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text("规则列表", size=14,
                                    weight=ft.FontWeight.W_500, color=THEME["text_color"]),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8)
                ),
                ft.ListView([
                    # 内置规则
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.BUILD, size=14,
                                    color=THEME["accent_color"]),
                            ft.Text(
                                "内置规则", size=12, weight=ft.FontWeight.W_500, color=THEME["accent_color"])
                        ], spacing=6),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6)
                    ),
                    self.builtin_rules_list,
                    # 全局规则
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PUBLIC, size=14,
                                    color=ft.Colors.BLUE_400),
                            ft.Text(
                                "全局规则", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_400)
                        ], spacing=6),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6)
                    ),
                    self.global_rules_list,
                    # 项目规则
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FOLDER_SPECIAL, size=14,
                                    color=ft.Colors.GREEN_400),
                            ft.Text(
                                "项目规则", size=12, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_400)
                        ], spacing=6),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6)
                    ),
                    self.project_rules_list,
                ], expand=True, spacing=0)
            ], spacing=0),
            width=280,
            bgcolor=THEME["sidebar_bg"],
            border=ft.Border(right=ft.BorderSide(1, THEME["border_color"]))
        )

        # 右侧编辑区域
        right_panel = ft.Container(
            content=ft.Column([
                # 规则元信息 - 使用固定布局
                ft.Row([
                    ft.Container(content=self.name_field, expand=3),
                    ft.Container(content=self.desc_field, expand=5),
                    ft.Container(content=self.priority_field, width=90),
                    ft.Container(content=self.enabled_switch, width=80)
                ], spacing=16),
                ft.Divider(color=THEME["border_color"], height=1),
                # 内容编辑器和预览
                ft.Stack([
                    self.content_editor,
                    self.preview_container
                ], expand=True)
            ], spacing=12),
            padding=ft.Padding.all(20),
            expand=True
        )

        self.controls = [
            header,
            dir_hint,
            ft.Divider(color=THEME["border_color"], height=1),
            ft.Row([
                left_panel,
                right_panel
            ], expand=True)
        ]

        # 加载规则列表
        self._load_rules_list()

    def _load_rules_list(self):
        """加载规则列表，按级别分组"""
        self.builtin_rules_list.controls.clear()
        self.global_rules_list.controls.clear()
        self.project_rules_list.controls.clear()

        rules = self.rules_manager.list_rules()

        # 按级别分组
        builtin_rules = [r for r in rules if r.level == "builtin"]
        global_rules = [r for r in rules if r.level == "global"]
        project_rules = [r for r in rules if r.level == "project"]

        # 加载内置规则
        if builtin_rules:
            for rule in builtin_rules:
                self.builtin_rules_list.controls.append(
                    self._create_rule_item(rule))
        else:
            self.builtin_rules_list.controls.append(
                self._create_empty_item("无内置规则"))

        # 加载全局规则
        if global_rules:
            for rule in global_rules:
                self.global_rules_list.controls.append(
                    self._create_rule_item(rule))
        else:
            self.global_rules_list.controls.append(
                self._create_empty_item("无全局规则"))

        # 加载项目规则
        if project_rules:
            for rule in project_rules:
                self.project_rules_list.controls.append(
                    self._create_rule_item(rule))
        else:
            self.project_rules_list.controls.append(
                self._create_empty_item("点击 新建 创建"))

    def _create_empty_item(self, text: str) -> ft.Container:
        """创建空项提示"""
        return ft.Container(
            content=ft.Text(text, size=11, color=THEME["secondary_text"]),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6)
        )

    def _create_rule_item(self, rule: Rule) -> ft.Container:
        """创建规则列表项"""
        is_selected = self.current_rule and self.current_rule.name == rule.name

        # 根据级别设置颜色
        level_colors = {
            "builtin": THEME["accent_color"],
            "global": ft.Colors.BLUE_400,
            "project": ft.Colors.GREEN_400
        }
        level_color = level_colors.get(rule.level, THEME["text_color"])

        # 内置规则不允许删除
        can_delete = rule.level != "builtin"

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        rule.name,
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=THEME["text_color"]
                    ),
                    ft.Text(
                        rule.description or "无描述",
                        size=10,
                        color=THEME["secondary_text"]
                    )
                ], spacing=1, expand=True),
                ft.Row([
                    # 级别标签
                    ft.Container(
                        content=ft.Text(
                            rule.level[0].upper(),  # 首字母
                            size=9,
                            color=level_color
                        ),
                        padding=ft.Padding.symmetric(horizontal=4, vertical=1),
                        border=ft.Border.all(1, level_color),
                        border_radius=4
                    ),
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if rule.enabled else ft.Icons.CIRCLE_OUTLINE,
                        size=14,
                        color=THEME["accent_color"] if rule.enabled else THEME["secondary_text"]
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=ft.Colors.RED_400 if can_delete else THEME["secondary_text"],
                        icon_size=16,
                        tooltip="删除" if can_delete else "内置规则不可删除",
                        on_click=lambda e, r=rule: self._on_delete_rule(
                            r) if can_delete else None
                    ) if can_delete else ft.Container(width=32)
                ], spacing=4)
            ], alignment=ft.MainAxisAlignment.START),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            bgcolor=THEME["selected_bg"] if is_selected else None,
            border_radius=4,
            on_click=lambda e, r=rule: self._on_select_rule(r)
        )

    def _on_select_rule(self, rule: Rule):
        """选择规则"""
        self.current_rule = rule
        self.name_field.value = rule.name
        self.desc_field.value = rule.description
        self.priority_field.value = str(rule.priority)
        self.enabled_switch.value = rule.enabled
        self.content_editor.value = rule.content

        self._load_rules_list()  # 刷新列表高亮
        self.update()

    def _on_new_rule(self, e):
        """新建规则"""
        self.current_rule = None
        self.name_field.value = ""
        self.desc_field.value = ""
        self.priority_field.value = "0"
        self.enabled_switch.value = True
        self.content_editor.value = ""

        self._load_rules_list()
        self.update()

    def _on_save(self, e):
        """保存规则"""
        if not self.name_field.value:
            _show_snack_bar(self.page, "请输入规则名称")
            return

        try:
            priority = int(self.priority_field.value or "0")
        except ValueError:
            priority = 0

        success = self.rules_manager.save_rule(
            name=self.name_field.value,
            description=self.desc_field.value or "",
            content=self.content_editor.value or "",
            priority=priority,
            enabled=self.enabled_switch.value
        )

        if success:
            _show_snack_bar(self.page, f"规则 '{self.name_field.value}' 已保存")
            self._load_rules_list()
            self.update()
        else:
            _show_snack_bar(self.page, "保存失败")

    def _on_delete_rule(self, rule: Rule):
        """删除规则"""
        def confirm_delete(e):
            success = self.rules_manager.delete_rule(rule.name)
            if success:
                _show_snack_bar(self.page, f"规则 '{rule.name}' 已删除")
                if self.current_rule and self.current_rule.name == rule.name:
                    self._on_new_rule(None)
                else:
                    self._load_rules_list()
                    self.update()
            self.page.pop_dialog()

        def on_cancel(e):
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("确认删除", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Text(
                    f"确定要删除规则 '{rule.name}' 吗？",
                    color=THEME["text_color"]
                ),
                width=400
            ),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.ElevatedButton(
                    "删除", on_click=confirm_delete,
                    bgcolor=ft.Colors.RED_400,
                    color=ft.Colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=20
        )

        self.page.show_dialog(dialog)

    def _on_close(self, e):
        """关闭视图"""
        if self.on_close:
            self.on_close()

    def _toggle_preview(self, e):
        """切换编辑/预览模式"""
        self.is_preview_mode = not self.is_preview_mode

        if self.is_preview_mode:
            # 切换到预览模式
            self.content_preview.value = self.content_editor.value or ""
            self.content_editor.visible = False
            self.preview_container.visible = True
            self.toggle_preview_btn.content = ft.Row([
                ft.Icon(ft.Icons.EDIT, size=18),
                ft.Text("编辑", size=14)
            ])
        else:
            # 切换到编辑模式
            self.content_editor.visible = True
            self.preview_container.visible = False
            self.toggle_preview_btn.content = ft.Row([
                ft.Icon(ft.Icons.PREVIEW, size=18),
                ft.Text("预览", size=14)
            ])

        self.update()
