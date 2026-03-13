"""
项目管理视图
"""

from pathlib import Path
from typing import Callable
import flet as ft

from core.config_manager import get_config_manager
from theme import THEME

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
    logger = get_logger("project_manager_view")

    error_msg = str(error)
    context_str = f" [{context}]" if context else ""
    logger.error(f"错误{context_str}: {error_msg}\n{traceback.format_exc()}")
    _show_snack_bar(page, f"错误{context_str}: {error_msg}", duration=5000)


class ProjectManagerView(ft.Column):
    """项目管理视图"""

    def __init__(self, on_close: Callable = None, on_project_changed: Callable = None):
        super().__init__()
        self.on_close = on_close
        self.on_project_changed = on_project_changed

        self.spacing = 0
        self.expand = True

        self.global_skills_dir = _config.get_global_skills_dir()

        # 标题栏
        header = ft.Container(
            content=ft.Row([
                ft.Text("项目管理", size=20,
                        weight=ft.FontWeight.W_600, color=THEME["text_color"]),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD, size=18),
                            ft.Text("添加", size=14)
                        ]),
                        bgcolor=THEME["accent_color"],
                        color=ft.Colors.WHITE,
                        on_click=self._show_add_dialog
                    ),
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

        # 全局技能/规则路径设置
        self.skills_dir_text = ft.Text(
            self.global_skills_dir or "未设置",
            size=14,
            color=THEME["text_color"]
        )

        skills_dir_section = ft.Container(
            content=ft.Column([
                ft.Text("全局技能/规则路径", size=14,
                        weight=ft.FontWeight.W_500, color=THEME["text_color"]),
                ft.Text("技能存放于 skills/ 子目录，规则存放于 rules/ 子目录",
                        size=11, color=THEME["secondary_text"]),
                ft.Row([
                    self.skills_dir_text,
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=THEME["accent_color"],
                        tooltip="修改",
                        on_click=self._show_skills_dir_dialog
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=4),
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            bgcolor=THEME["hover_bg"],
            border_radius=8,
            margin=ft.Margin.symmetric(horizontal=20, vertical=8)
        )

        # 项目列表
        self.project_list = ft.ListView(
            spacing=8,
            padding=ft.Padding.symmetric(horizontal=20),
            expand=True
        )

        self.controls = [
            header,
            ft.Divider(color=THEME["border_color"], height=1),
            skills_dir_section,
            ft.Container(
                content=ft.Text("项目列表", size=14,
                                weight=ft.FontWeight.W_500, color=THEME["text_color"]),
                padding=ft.Padding.symmetric(horizontal=20, vertical=12)
            ),
            self.project_list
        ]

        self._load_projects()

    def _load_projects(self):
        """加载项目列表"""
        self.project_list.controls.clear()
        projects = _config.get_projects_list()

        for project in projects:
            card = self._create_project_card(project)
            self.project_list.controls.append(card)

    def _create_project_card(self, project: dict) -> ft.Card:
        """创建项目卡片"""
        path = project.get("path", "")
        name = project.get("name", "未命名")
        is_current = project.get("is_current", False)

        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.FOLDER_SPECIAL if is_current else ft.Icons.FOLDER,
                        color=THEME["accent_color"] if is_current else THEME["secondary_text"]
                    ),
                    ft.Column([
                        ft.Text(
                            name,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=THEME["text_color"]
                        ),
                        ft.Text(
                            path,
                            size=11,
                            color=THEME["secondary_text"]
                        )
                    ], spacing=4, expand=True),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE if is_current else ft.Icons.CHECK_CIRCLE_OUTLINE,
                            icon_color=THEME["accent_color"] if is_current else THEME["secondary_text"],
                            tooltip="切换到此项目" if not is_current else "当前项目",
                            on_click=lambda e,
                            p=path: self._switch_project(p) if not is_current else None
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_400,
                            tooltip="删除",
                            on_click=lambda e,
                            p=path: self._confirm_delete(p)
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.START),
                padding=16
            ),
            bgcolor=THEME["selected_bg"] if is_current else THEME["hover_bg"]
        )

    def _show_add_dialog(self, e):
        """显示添加项目对话框"""
        path_field = ft.TextField(
            label="项目路径",
            hint_text="/path/to/project",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            expand=True,
            dense=True
        )

        async def on_browse(e):
            """浏览文件夹 - 待 Flet 修复 FilePicker 后启用"""
            _show_snack_bar(self.page, "暂不支持文件夹选择，请手动输入路径")

        def on_add(e):
            if path_field.value:
                result = _config.add_project(
                    path_field.value, Path(path_field.value).name)
                if result:
                    _show_snack_bar(
                        self.page, f"已添加项目: {Path(path_field.value).name}")
                    self.page.pop_dialog()
                    self._load_projects()
                    self.update()
                else:
                    _show_snack_bar(self.page, "项目已存在")

        def on_cancel(e):
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("添加项目", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Row([
                    path_field,
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        icon_color=THEME["accent_color"],
                        tooltip="浏览",
                        on_click=on_browse
                    )
                ], spacing=8),
                width=500
            ),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.ElevatedButton(
                    "添加", on_click=on_add,
                    bgcolor=THEME["accent_color"],
                    color=ft.Colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=20
        )

        self.page.show_dialog(dialog)

    def _show_skills_dir_dialog(self, e):
        """显示设置全局技能/规则路径对话框"""
        dir_field = ft.TextField(
            label="全局技能/规则路径",
            value=self.global_skills_dir or "",
            hint_text="/path/to/global",
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            expand=True,
            dense=True
        )

        async def on_browse(e):
            """浏览文件夹 - 待 Flet 修复 FilePicker 后启用"""
            _show_snack_bar(self.page, "暂不支持文件夹选择，请手动输入路径")

        def on_save(e):
            if dir_field.value:
                _config.set_global_skills_dir(dir_field.value)
                self.global_skills_dir = dir_field.value
                self.skills_dir_text.value = dir_field.value
                _show_snack_bar(self.page, "全局技能/规则路径已设置")
                self.page.pop_dialog()
                self.update()

        dialog = ft.AlertDialog(
            title=ft.Text("设置全局技能/规则路径", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("技能将存放到 skills/ 子目录，规则将存放到 rules/ 子目录",
                            size=12, color=THEME["secondary_text"]),
                    ft.Row([
                        dir_field,
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            icon_color=THEME["accent_color"],
                            tooltip="浏览",
                            on_click=on_browse
                        )
                    ], spacing=8)
                ], spacing=12),
                width=500
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.pop_dialog()),
                ft.ElevatedButton(
                    "保存", on_click=on_save,
                    bgcolor=THEME["accent_color"],
                    color=ft.Colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=20
        )

        self.page.show_dialog(dialog)

    def _switch_project(self, project_path: str):
        """切换项目"""
        _config.set_current_project_path(project_path)
        self._load_projects()
        self.update()
        _show_snack_bar(self.page, f"已切换到项目")
        if self.on_project_changed:
            self.on_project_changed(project_path)

    def _confirm_delete(self, project_path: str):
        """确认删除项目"""
        def on_delete(e):
            _config.remove_project(project_path)
            _show_snack_bar(self.page, "项目已删除")
            self.page.pop_dialog()
            self._load_projects()
            self.update()

        dialog = ft.AlertDialog(
            title=ft.Text("确认删除", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Text("确定要从列表中移除这个项目吗？", color=THEME["text_color"]),
                width=400
            ),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.page.pop_dialog()),
                ft.ElevatedButton(
                    "删除", on_click=on_delete,
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
