# AI Agent 桌面应用

基于 Flet (Flutter) 的 AI Agent 桌面应用，支持智能对话、技能扩展和项目管理。

## ✨ 特性

- 🎨 **现代化 UI** - 采用 ChatGPT 风格深色主题，视觉舒适
- 💬 **智能对话** - 支持流式响应，实时显示 AI 回复
- 🔧 **技能系统** - 可扩展的技能体系，支持全局和项目级技能
- 📁 **项目管理** - 多项目管理，自动切换项目上下文
- 📜 **规则系统** - 支持内置、全局和项目三级规则
- 🚀 **高效工具** - 内置文件操作、代码分析、Git 等实用工具

## 目录结构

```
.
├── main.py              # 应用主入口
├── config.py            # 配置管理
├── llm_factory.py       # LLM 工厂
├── theme/               # 主题配置
│   └── __init__.py      # 主题颜色定义
├── components/          # UI 组件
│   ├── message_bubble.py    # 消息气泡
│   ├── markdown_viewer.py   # Markdown 渲染
│   ├── sidebar.py           # 侧边栏
│   ├── status_indicator.py  # 状态指示器
│   └── suggestion_popup.py  # 智能提示
├── views/               # 页面视图
│   ├── chat_view.py         # 聊天视图
│   ├── model_config_view.py # 模型配置
│   ├── project_manager_view.py # 项目管理
│   ├── rules_manager_view.py   # 规则管理
│   └── skill_manager_view.py   # 技能管理
├── core/                # 核心逻辑
│   ├── agent/           # Agent 系统
│   │   ├── agent.py         # Agent 实现
│   │   ├── workflow.py      # 工作流
│   │   ├── state.py         # 状态管理
│   │   └── prompts/         # 提示词
│   ├── plan_framework.py
│   ├── settings.py
│   ├── skill_executor.py
│   └── skill_registry.py
├── tools/               # 工具系统
│   ├── file_tools.py        # 文件操作
│   ├── search_tools.py      # 搜索工具
│   ├── code_analysis_tools.py # 代码分析
│   ├── git_tools.py         # Git 工具
│   └── command_tools.py     # 命令执行
├── controllers/         # 控制器层
│   └── main_controller.py   # 主控制器
├── services/            # 服务层
│   ├── session_service.py   # 会话服务
│   └── project_service.py   # 项目服务
├── utils/               # 工具类
│   ├── logger.py          # 日志工具
│   └── rules_manager.py   # 规则管理器
├── requirements.txt     # 依赖
└── .env                 # 环境变量
```

## 运行方式

```bash
# 切换到 conda 环境
conda activate langchain

# 运行应用
python main.py
```

## 配置说明

### 1. 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# LLM API 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4

# 或使用其他兼容的 LLM
# DEEPSEEK_API_KEY=...
# BASE_URL=...
```

### 2. 模型配置

启动应用后，点击右上角「模型」按钮进行配置：
- 选择模型提供商（OpenAI / DeepSeek / Ollama 等）
- 输入 API Key
- 设置模型名称
- 调整温度参数

## 功能使用

### 智能对话

- 在底部输入框输入消息，按 Enter 发送
- Shift+Enter 换行
- 支持流式响应，实时查看 AI 回复

### 快捷命令

- `/help` - 显示帮助信息
- `/skills` - 查看可用技能
- `/rules` - 查看已启用规则

### 智能提示

- 输入 `/` 触发命令提示
- 输入 `@` 触发文件选择提示

### 项目管理

- 点击左下角项目下拉框切换项目
- 不同项目有独立的会话历史和规则配置

### 技能管理

- 点击顶部「技能」按钮
- 添加、编辑、删除技能
- 支持全局技能和项目技能

### 规则管理

- 点击顶部「规则」按钮
- 管理已启用的规则
- 支持内置规则、全局规则和项目规则

## 依赖

### 核心依赖
- flet >= 0.23.0       # GUI 框架
- langchain >= 0.2.0   # LangChain 框架
- langchain-openai     # OpenAI 支持
- langchain-deepseek   # DeepSeek 支持
- PyYAML               # YAML 解析
- python-dotenv        # 环境变量管理

### 打包依赖（可选）
如果需要使用 `flet pack` 打包成可执行程序，还需安装：
- **PyInstaller** >= 6.0.0  # Python 打包工具

安装命令：
```bash
pip install PyInstaller
```

完整依赖列表请查看 `requirements.txt`。

## 主题配色

采用 ChatGPT 风格深色主题（优化版）：

| 元素 | 颜色值 |
|------|--------|
| **页面背景** | `#2B2C35` |
| **侧边栏背景** | `#1A1C23` |
| **用户消息背景** | `#3E3F4F` |
| **AI 消息背景** | `transparent` (透明) |
| **强调色** | `#3DD68A` (清新绿) |
| **文本颜色** | `#ECECF1` |

## UI 优化亮点

- ✅ **用户消息右对齐** - 符合主流聊天软件习惯
- ✅ **纯白文字高对比** - 用户消息使用 `#FFFFFF` 纯白色
- ✅ **AI 消息透明融合** - 左侧强调边框标识
- ✅ **精致思考动画** - 波浪式跳动小圆点
- ✅ **流畅淡入效果** - 新消息平滑显示
- ✅ **Markdown 优化** - Monokai 代码主题，语法高亮清晰

## 开发规范

- 使用 Python 3.10+
- 遵循 PEP 8 代码规范
- 使用 type hints 增强代码可读性
- 重要操作需记录日志

---

## 🔧 开发教程

### 环境搭建

#### 1. 克隆项目

```bash
git clone <repository-url>
cd myagent
```

#### 2. 创建 Conda 环境

```bash
# 创建新环境
conda create -n aiagent python=3.10

# 激活环境
conda activate aiagent
```

#### 3. 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 验证安装
python -c "import flet; print(f'Flet version: {flet.__version__}')"
```

#### 4. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# OPENAI_API_KEY=sk-...
```

### 运行开发服务器

```bash
# 方式 1：直接运行
python main.py

# 方式 2：使用 Flet 运行（支持热重载）
flet run main.py

# 方式 3：在浏览器中运行
flet run main.py --port 8550
```

### 目录结构说明

#### 核心模块

- **`main.py`** - 应用主入口，负责初始化和事件分发
- **`controllers/`** - 控制器层，处理业务逻辑和用户交互
- **`views/`** - 视图层，负责 UI 展示
- **`components/`** - 可复用的 UI 组件
- **`services/`** - 服务层，提供数据持久化和业务服务
- **`core/`** - 核心业务逻辑，包括 Agent、技能、工具系统

#### 数据流

```
用户操作 → View (UI) → Controller (逻辑) → Service (数据) → Core (业务)
                                      ↓
                                   Model (状态)
```

### 添加新功能

#### 示例：添加新的视图

1. **创建视图文件** `views/my_view.py`:

```python
import flet as ft
from theme import THEME

class MyView(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Text("我的视图")
        self.expand = True
```

2. **在主应用中注册** `main.py`:

```python
from views.my_view import MyView

# 在 _build_ui() 中添加
self.my_view = MyView()
self.page.add(self.my_view)
```

#### 示例：添加新的工具

1. **创建工具文件** `tools/my_tool.py`:

```python
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的工具描述"
    
    async def execute(self, **kwargs):
        # 实现工具逻辑
        return "执行结果"
```

2. **注册到工具系统**:

在相应的注册表中添加工具类。

### 调试技巧

#### 1. 使用日志

```python
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("信息级别日志")
logger.debug("调试级别日志")
logger.error("错误级别日志")
```

#### 2. 查看控制台输出

- Flet 会在终端输出详细的运行日志
- 错误信息会显示完整的堆栈跟踪
- 可以使用 `print()` 快速调试（不推荐生产代码）

#### 3. 使用断点调试

```bash
# 使用 pdb 调试
python -m pdb main.py

# 或在代码中设置断点
import pdb; pdb.set_trace()
```

### 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行特定测试文件
python test_simple.py

# 生成覆盖率报告
pytest --cov=myagent tests/
```

### 代码风格检查

```bash
# 使用 flake8 检查代码风格
flake8 .

# 使用 black 格式化代码
black .

# 使用 isort 排序导入
isort .
```

---

## 📦 打包教程

### 快速打包（推荐）

项目提供了自动化打包脚本，一键生成可执行文件。

#### Linux / macOS

```bash
# 进入项目目录
cd /home/alger/workspace/myagent

# 执行打包脚本
chmod +x build.sh
./build.sh
```

#### Windows

双击运行 `build.bat` 或在命令行执行：

```cmd
cd C:\path\to\myagent
build.bat
```

### 手动打包

#### 安装打包工具

```bash
pip install flet
```

#### Windows 打包命令

```bash
flet pack main.py ^
  --name "AI Agent" ^
  --add-data "theme;theme" ^
  --add-data "components;components" ^
  --add-data "views;views" ^
  --add-data "core;core" ^
  --add-data "tools;tools" ^
  --add-data "controllers;controllers" ^
  --add-data "services;services" ^
  --add-data "utils;utils" ^
  --hidden-import langchain ^
  --hidden-import yaml
```

#### macOS / Linux 打包命令

```bash
flet pack main.py \
  --name "AI Agent" \
  --add-data "theme:theme" \
  --add-data "components:components" \
  --add-data "views:views" \
  --add-data "core:core" \
  --add-data "tools:tools" \
  --add-data "controllers:controllers" \
  --add-data "services:services" \
  --add-data "utils:utils" \
  --hidden-import langchain \
  --hidden-import yaml
```

### 打包参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--name` | 应用名称 | `"AI Agent"` |
| `--add-data` | 包含数据文件 | `"theme:theme"` (Unix) |
| `--hidden-import` | 隐式导入模块 | `langchain` |
| `--icon` | 应用图标 | `"assets/icon.ico"` |
| `--file-version` | 文件版本 | `"1.0.0"` |

### 打包产物

打包成功后会在 `dist/` 目录生成：

```
dist/
└── AI Agent/
    ├── AI Agent(.exe)     # 可执行文件
    ├── theme/             # 主题资源
    ├── components/        # UI 组件
    ├── views/            # 页面视图
    └── ...               # 其他依赖
```

**文件大小**: 约 150-250 MB（包含 Python 运行时和所有依赖）

### 运行打包后的程序

```bash
# Linux / macOS
cd dist/AI\ Agent
./AI\ Agent

# Windows
cd dist\AI Agent
AI Agent.exe
```

### 自定义图标

#### Windows (.ico)

```bash
# 准备 256x256 PNG 转换为 ICO
convert icon.png icon.ico
```

#### macOS (.icns)

```bash
# 创建 iconset
mkdir icon.iconset
sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
iconutil -c icns icon.iconset
```

#### Linux (.png)

直接使用 512x512 的 PNG 文件即可。

### 创建安装包（可选）

#### macOS: 创建 DMG

```bash
brew install create-dmg
create-dmg \
  --volname "AI Agent" \
  --window-size 600 400 \
  "AI-Agent-1.0.0.dmg" \
  "dist/AI Agent.app"
```

#### Windows: 创建 MSI

使用 Advanced Installer 或 Inno Setup 创建 MSI 安装包。

#### Linux: 创建 AppImage

```bash
linuxdeploy \
  --appdir AppDir \
  --executable dist/AI\ Agent/AI\ Agent \
  --output appimage
```

### 发布到 GitHub Releases

1. **打标签**:

```bash
git tag v1.0.0
git push origin v1.0.0
```

2. **上传产物**:

在 GitHub Releases 页面上传各平台的安装包：
- `AI-Agent-Windows.zip`
- `AI-Agent-macOS.dmg`
- `AI-Agent-Linux.AppImage`

3. **编写发布说明**:

```markdown
## AI Agent v1.0.0

### 新特性
- ✨ 首次发布
- 🎨 现代化 UI 界面
- 💬 智能对话功能

### 下载
- [Windows 版本](链接)
- [macOS 版本](链接)
- [Linux 版本](链接)

### 使用说明
1. 下载对应系统的安装包
2. 安装后运行
3. 配置 LLM API Key
4. 开始使用！
```

---

## 📚 更多文档

- **详细打包指南**: [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)
- **快速打包教程**: [QUICK_PACKAGING.md](QUICK_PACKAGING.md)
- **打包设置报告**: [PACKAGING_SETUP_REPORT.md](PACKAGING_SETUP_REPORT.md)

---

## 常见问题

### Q: AI 不回复怎么办？

A: 检查以下几点：
1. 确认已正确配置 LLM API Key
2. 检查网络连接
3. 查看控制台日志了解错误信息

### Q: 如何添加自定义技能？

A: 点击顶部「技能」→「新建技能」，编写技能描述和实现代码。

### Q: 如何切换项目？

A: 点击左下角项目下拉框，选择目标项目即可。

---

*最后更新：2026-03-12*
