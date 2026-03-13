"""
Skill 管理视图
"""

from typing import Callable
import flet as ft

from core.skill_registry import get_skill_registry, Skill
from theme import THEME
from components.markdown_viewer import MarkdownViewer


def _show_snack_bar(page, message: str, duration: int = 3000):
    """显示 SnackBar"""
    try:
        snack = ft.SnackBar(content=ft.Text(message), duration=duration)
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception:
        pass  # 避免递归错误


def handle_view_error(page, error: Exception, context: str = ""):
    """视图错误处理"""
    import traceback
    from utils.logger import get_logger
    logger = get_logger("skill_manager_view")

    error_msg = str(error)
    context_str = f" [{context}]" if context else ""
    logger.error(f"错误{context_str}: {error_msg}\n{traceback.format_exc()}")
    _show_snack_bar(page, f"错误{context_str}: {error_msg}", duration=5000)


class SkillManagerView(ft.Column):
    """Skill 管理视图"""

    def __init__(self, on_close: Callable = None):
        super().__init__()
        self.on_close = on_close
        self.registry = get_skill_registry()

        self.spacing = 0
        self.expand = True

        # 标题栏
        header = ft.Container(
            content=ft.Row([
                ft.Text("Skill 管理", size=20,
                        weight=ft.FontWeight.W_600, color=THEME["text_color"]),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD, size=18),
                            ft.Text("新建", size=14)
                        ]),
                        bgcolor=THEME["accent_color"],
                        color=ft.Colors.WHITE,
                        on_click=self._show_create_dialog
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.REFRESH, size=18),
                            ft.Text("刷新", size=14)
                        ]),
                        bgcolor=THEME["hover_bg"],
                        color=THEME["text_color"],
                        on_click=self._reload_all
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

        # Skill 列表
        self.skill_list = ft.ListView(
            spacing=8,
            padding=ft.Padding.symmetric(horizontal=20),
            expand=True
        )

        self.controls = [
            header,
            ft.Divider(color=THEME["border_color"], height=1),
            self.skill_list
        ]

        try:
            self._load_skills()
        except Exception as e:
            handle_view_error(self.page, e, "初始化加载 Skills")

    def _load_skills(self):
        """加载 Skill 列表，按级别分组"""
        try:
            self.skill_list.controls.clear()
            skills = self.registry.list_skills()
        except Exception as e:
            handle_view_error(self.page, e, "加载 Skills")
            return

        # 按级别分组
        builtin_skills = [s for s in skills if s.level == "builtin"]
        global_skills = [s for s in skills if s.level == "global"]
        project_skills = [s for s in skills if s.level == "project"]

        # 添加分组标题和技能
        if builtin_skills:
            self.skill_list.controls.append(
                self._create_section_title("内置 Skills", ft.Icons.BUILD))
            for skill in builtin_skills:
                self.skill_list.controls.append(self._create_skill_card(skill))

        if global_skills:
            self.skill_list.controls.append(
                self._create_section_title("全局 Skills", ft.Icons.PUBLIC))
            for skill in global_skills:
                self.skill_list.controls.append(self._create_skill_card(skill))

        if project_skills:
            self.skill_list.controls.append(
                self._create_section_title("项目 Skills", ft.Icons.FOLDER_SPECIAL))
            for skill in project_skills:
                self.skill_list.controls.append(self._create_skill_card(skill))

        if not skills:
            self.skill_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "暂无 Skills",
                        size=12,
                        color=THEME["secondary_text"]
                    ),
                    padding=ft.Padding.all(20),
                    alignment=ft.Alignment.CENTER
                )
            )

        # 注意：不要在 __init__ 中调用 self.update()，控件还未添加到页面

    def _create_section_title(self, title: str, icon) -> ft.Container:
        """创建分组标题"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=16, color=THEME["accent_color"]),
                ft.Text(title, size=13, weight=ft.FontWeight.W_600,
                        color=THEME["accent_color"])
            ], spacing=8),
            padding=ft.Padding.symmetric(horizontal=8, vertical=12)
        )

    def _create_skill_card(self, skill: Skill) -> ft.Card:
        """创建 Skill 卡片"""
        # 根据级别设置颜色
        level_colors = {
            "builtin": THEME["accent_color"],
            "global": ft.Colors.BLUE_400,
            "project": ft.Colors.GREEN_400
        }
        level_icon = level_colors.get(skill.level, THEME["accent_color"])

        # 内置 skill 不允许删除
        can_delete = skill.level != "builtin"

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.EXTENSION, color=level_icon),
                        ft.Column([
                            ft.Text(
                                skill.metadata.name,
                                size=15,
                                weight=ft.FontWeight.W_500,
                                color=THEME["text_color"]
                            ),
                            ft.Text(
                                skill.metadata.description or "无描述",
                                size=11,
                                color=THEME["secondary_text"]
                            )
                        ], spacing=2, expand=True),
                        ft.Row([
                            # 级别标签
                            ft.Container(
                                content=ft.Text(
                                    skill.level.upper(),
                                    size=10,
                                    color=THEME["secondary_text"]
                                ),
                                padding=ft.Padding.symmetric(
                                    horizontal=8, vertical=2),
                                bgcolor=THEME["bg_color"],
                                border_radius=4
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=THEME["text_color"],
                                icon_size=18,
                                tooltip="重新加载",
                                on_click=lambda e, s=skill: self._reload_skill(
                                    s)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                icon_color=THEME["accent_color"],
                                icon_size=18,
                                tooltip="查看内容",
                                on_click=lambda e, s=skill: self._show_skill_detail(
                                    s)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=ft.Colors.RED_400 if can_delete else THEME["secondary_text"],
                                icon_size=18,
                                tooltip="删除" if can_delete else "内置 Skill 不可删除",
                                on_click=lambda e, s=skill: self._confirm_delete(
                                    s) if can_delete else None
                            ) if can_delete else ft.Container(width=40)
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.START),
                ]),
                padding=12
            ),
            bgcolor=THEME["hover_bg"]
        )

    def _show_create_dialog(self, e):
        """显示创建 Skill 对话框"""
        name_field = ft.TextField(
            label="Skill 名称",
            hint_text="例如: my-skill（只能包含小写字母、数字和连字符）",
            border_color=THEME["border_color"],
            color=THEME["text_color"]
        )
        desc_field = ft.TextField(
            label="描述",
            hint_text="Skill 的功能描述",
            border_color=THEME["border_color"],
            color=THEME["text_color"]
        )
        instructions_field = ft.TextField(
            label="使用说明 (Markdown)",
            hint_text="详细的使用说明和指导信息...",
            multiline=True,
            min_lines=15,
            border_color=THEME["border_color"],
            color=THEME["text_color"],
            expand=True
        )

        def on_create(e):
            if name_field.value and desc_field.value:
                # 自动生成规范的 SKILL.md 格式
                skill_md_content = f"""---
name: {name_field.value}
description: {desc_field.value}
version: "1"
---

{instructions_field.value or ''}
"""
                from tools.skill_tools import create_skill
                result = create_skill.invoke({
                    "name": name_field.value,
                    "description": desc_field.value,
                    "skill_md_content": skill_md_content
                })
                _show_snack_bar(self.page, result)
                self.page.pop_dialog()
                self._load_skills()
                self.update()
            else:
                _show_snack_bar(self.page, "请填写 Skill 名称和描述")

        def on_cancel(e):
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("创建 Skill", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column([
                    name_field,
                    desc_field,
                    instructions_field
                ], spacing=8, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
                width=600,
                height=450
            ),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
                ft.ElevatedButton(
                    "创建", on_click=on_create,
                    bgcolor=THEME["accent_color"],
                    color=ft.Colors.WHITE
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=20
        )

        self.page.show_dialog(dialog)

    def _reload_skill(self, skill: Skill):
        """重新加载 Skill"""
        result = self.registry.reload_skill(skill.metadata.name)
        if result:
            _show_snack_bar(
                self.page, f"Skill '{skill.metadata.name}' 已重新加载")
            self._load_skills()
            self.update()
        else:
            _show_snack_bar(self.page, "重新加载失败")

    def _confirm_delete(self, skill: Skill):
        """确认删除 Skill"""
        def on_delete(e):
            from tools.skill_tools import delete_skill
            result = delete_skill.invoke(
                {"name": skill.metadata.name, "confirm": True})
            _show_snack_bar(self.page, result)
            self.page.pop_dialog()
            self._load_skills()
            self.update()

        def on_cancel(e):
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            title=ft.Text("确认删除", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Text(
                    f"确定要删除 Skill '{skill.metadata.name}' 吗？",
                    color=THEME["text_color"]
                ),
                width=400
            ),
            actions=[
                ft.TextButton("取消", on_click=on_cancel),
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

    def _reload_all(self, e):
        """重新加载所有 Skills"""
        self.registry.discover_skills()
        self._load_skills()
        self.update()
        _show_snack_bar(self.page, "所有 Skills 已重新加载")

    def _on_close(self, e):
        """关闭视图"""
        if self.on_close:
            self.on_close()

    def _show_skill_detail(self, skill: Skill):
        """显示 Skill 详情对话框"""
        def on_close_dialog(e):
            self.page.pop_dialog()

        # 创建 Markdown 预览组件
        md_viewer = MarkdownViewer(
            value=skill.instructions or "无内容",
            selectable=True
        )

        dialog = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.EXTENSION, color=THEME["accent_color"]),
                ft.Text(
                    skill.metadata.name,
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=THEME["text_color"]
                ),
                ft.Container(
                    content=ft.Text(
                        skill.level.upper(),
                        size=10,
                        color=THEME["secondary_text"]
                    ),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    bgcolor=THEME["bg_color"],
                    border_radius=4
                )
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    # 描述
                    ft.Text(
                        skill.metadata.description or "无描述",
                        size=12,
                        color=THEME["secondary_text"]
                    ),
                    ft.Divider(color=THEME["border_color"], height=1),
                    # Markdown 内容
                    ft.Container(
                        content=md_viewer,
                        expand=True,
                        padding=ft.Padding.all(8),
                        bgcolor=THEME["bg_color"],
                        border=ft.Border.all(1, THEME["border_color"]),
                        border_radius=4
                    )
                ], spacing=12, scroll=ft.ScrollMode.AUTO),
                width=650,
                height=450
            ),
            actions=[
                ft.TextButton("关闭", on_click=on_close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            inset_padding=20
        )

        self.page.show_dialog(dialog)
