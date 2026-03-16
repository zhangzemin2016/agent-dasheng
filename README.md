# Agent Dasheng - AI Agent 桌面应用

基于 Flet、LangChain 和 LangGraph 的智能 AI Agent 桌面应用，支持智能对话、技能扩展、项目管理和代码分析。

## ✨ 特性

- 🎨 **现代化 UI** - ChatGPT 风格深色主题，视觉舒适
- 💬 **智能对话** - 基于 LangGraph 的流式响应，实时显示 AI 回复
- 🔧 **技能系统** - 可扩展的技能体系，支持全局和项目级技能
- 📁 **项目管理** - 多项目管理，自动切换项目上下文
- 📜 **规则系统** - 支持内置、全局和项目三级规则配置
- 🛠️ **丰富工具** - 15+ 内置工具（文件/目录/命令/搜索）
- 🧠 **DashengAgent** - 自研 Agent 框架（LangChain + LangGraph）
- 📝 **Prompt DSL** - YAML 模板驱动的提示词管理

## 📁 项目结构

```
.
├── main.py                 # 应用主入口
├── agent/                  # Agent 系统
│   ├── dasheng_agent.py    # DashengAgent 核心（LangGraph）
│   ├── deep_agent.py       # DeepAgent 封装（向后兼容）
│   └── tools/              # 工具集（按功能分类）
│       ├── file_tools.py   # 文件操作（5 个工具）
│       ├── directory_tools.py # 目录操作（4 个工具）
│       ├── command_tools.py   # 命令执行（3 个工具）
│       ├── search_tools.py    # 搜索功能（3 个工具）
│       ├── code_tools.py   # 代码分析工具
│       ├── git_tools.py    # Git 操作工具
│       └── network_tools.py # 网络访问工具
├── components/             # UI 组件
│   ├── message_bubble.py   # 消息气泡
│   ├── markdown_viewer.py  # Markdown 渲染
│   ├── sidebar.py          # 侧边栏
│   ├── status_indicator.py # 状态指示器
│   └── suggestion_popup.py # 智能提示
├── views/                  # 页面视图
│   ├── chat_view.py        # 聊天视图
│   ├── model_config_view.py # 模型配置
│   ├── project_manager_view.py # 项目管理
│   ├── rules_manager_view.py   # 规则管理
│   └── skill_manager_view.py   # 技能管理
├── core/                   # 核心逻辑
│   ├── config_manager.py   # 配置管理
│   ├── plan_framework.py   # 计划框架
│   ├── skill_executor.py   # 技能执行器
│   ├── skill_registry.py   # 技能注册表
│   ├── prompt_manager.py   # 提示词管理器
│   └── prompts/            # Prompt DSL 系统
│       ├── loader.py       # 模板加载器
│       ├── prompt_registry.py # 模板注册表
│       └── templates/      # YAML 模板（精简版）
│           ├── role.yaml
│           ├── capabilities.yaml
│           ├── tools.yaml
│           └── task_strategy.yaml
├── controllers/            # 控制器层
│   └── main_controller.py  # 主控制器
├── services/               # 服务层
│   ├── session_service.py  # 会话服务
│   └── project_service.py  # 项目服务
├── storage/                # 数据存储
│   ├── database.py         # 数据库操作
│   └── session_storage.py  # 会话存储
├── utils/                  # 工具类
│   ├── logger.py           # 日志工具
│   └── rules_manager.py    # 规则管理器
├── config/                 # 配置文件
│   ├── settings.json       # 应用设置
│   ├── llm_config.json     # LLM 配置
│   └── app_config.json     # 应用配置
├── theme/                  # 主题配置
├── constants/              # 常量定义
├── requirements.txt        # Python 依赖
├── build.sh                # Linux/macOS 打包脚本
└── build.bat               # Windows 打包脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Conda 环境（推荐）

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd agent-dasheng
```

2. **创建并激活 Conda 环境**

```bash
conda create -n langchain python=3.10
conda activate langchain
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **运行应用**

```bash
python main.py
```

## ⚙️ 配置说明

### LLM 配置

启动应用后，点击顶部「模型」按钮进行配置：

- **模型提供商**: OpenAI、DeepSeek、Ollama 等
- **API Key**: 对应平台的 API 密钥
- **模型名称**: 如 gpt-4、deepseek-chat 等
- **温度参数**: 控制生成随机性 (0-1)

配置信息保存在 `config/llm_config.json` 中。

### 项目管理

- 点击顶部「项目」按钮管理项目
- 支持添加多个项目路径
- 不同项目拥有独立的会话历史和规则配置

项目列表保存在 `config/settings.json` 中。

## 🎯 功能使用

### 🛠️ 工具系统

内置 **15+ 个工具**，按功能分类，支持自动调用：

### 📁 文件操作（5 个工具）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `read_file` | 读取文件内容 | 读取 README.md |
| `write_file` | 写入文件 | 创建新文件 |
| `edit_file` | 编辑文件 | 替换文本 |
| `delete_file` | 删除文件 | 删除临时文件 |
| `copy_file` | 复制文件 | 备份文件 |

### 📂 目录操作（4 个工具）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `list_directory` | 列出目录内容 | 查看项目结构 |
| `create_directory` | 创建目录 | 新建文件夹 |
| `delete_directory` | 删除目录 | 清理目录 |
| `move_path` | 移动文件或目录 | 重命名/移动 |

### ⚡ 命令执行（3 个工具）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `execute_command` | 执行 Shell 命令 | 运行代码、安装依赖 |
| `run_python` | 运行 Python 代码 | 执行代码片段 |
| `run_script` | 运行脚本文件 | 执行脚本 |

### 🔍 搜索（3 个工具）

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `search_files` | 搜索文件 | 查找 *.py 文件 |
| `search_content` | 搜索文件内容 | grep 功能 |
| `find_in_files` | 在指定文件中搜索 | 多文件搜索 |

**工具调用示例**：
```python
# LLM 自动调用工具
用户：读取 README.md 文件
→ 调用 read_file(file_path="README.md")
→ 返回文件内容
```

**安全检查**：
- ✅ 禁止危险命令（rm -rf, sudo 等）
- ✅ 命令超时保护（默认 30 秒）
- ✅ 文件操作确认（删除需 confirm=True）

## 📝 Prompt DSL 系统

自研的提示词管理系统，从 Markdown 迁移到 YAML 模板：

**核心优势**:
- ✅ **版本控制** - Git diff 清晰
- ✅ **变量插值** - `{{variable}}`
- ✅ **条件加载** - 环境变量控制
- ✅ **模板复用** - 一次定义多处使用

**架构分层**:
```
PromptManager（统一入口）
    ↓
PromptRegistry（管理层）
    ↓
PromptLoader（加载层）
    ↓
PromptTemplate（渲染层）
```

**使用示例**:
```python
from core.prompt_manager import get_prompt_manager

manager = get_prompt_manager()
system_prompt = manager.build_system_prompt()
```

**模板语法**:
```yaml
config:
  name: role
  version: "3.0"

template: |
  # 智能助手
  当前环境：{{environment}}
  
  {%if ENABLE_DEBUG%}
  调试模式开启
  {%endif%}
```

更多信息：[`core/prompts/ARCHITECTURE.md`](core/prompts/ARCHITECTURE.md)

### 智能对话

- **发送消息**: 在底部输入框输入，按 Enter 发送
- **换行**: Shift + Enter
- **流式响应**: 实时查看 AI 回复内容
- **停止生成**: 点击停止按钮中断当前回复

### 快捷命令

输入 `/` 触发命令提示：

- `/help` - 显示帮助信息
- `/skills` - 查看可用技能
- `/rules` - 查看已启用规则

### 文件引用

输入 `@` 触发文件选择提示，快速引用项目中的文件。

### 工具能力

Agent 内置以下工具能力：

| 类别 | 工具 | 说明 |
|------|------|------|
| **文件操作** | ls, read_file, write_file, edit_file, glob, grep | 文件系统操作 |
| **代码分析** | check_syntax, analyze_dependencies, code_statistics | Python/Java 语法检查、依赖分析 |
| **Git 操作** | git_status, git_log, git_add, git_commit, git_push 等 | 完整的 Git 工作流 |
| **网络访问** | fetch_webpage, web_search, http_request | 网页获取、搜索、API 请求 |
| **任务管理** | write_todos, task | 任务规划和子代理调用 |

## 📦 打包发布

### 快速打包

项目提供自动化打包脚本：

**Linux / macOS:**
```bash
chmod +x build.sh
./build.sh
```

**Windows:**
```cmd
build.bat
```

打包成功后，可执行文件位于 `dist/AI Agent/` 目录。

### 手动打包

```bash
flet pack main.py \
  --name "AI Agent" \
  --add-data "theme:theme" \
  --add-data "components:components" \
  --add-data "views:views" \
  --add-data "core:core" \
  --add-data "agent:agent" \
  --add-data "controllers:controllers" \
  --add-data "services:services" \
  --add-data "utils:utils" \
  --add-data "storage:storage" \
  --add-data "config:config" \
  --add-data "constants:constants" \
  --hidden-import langchain \
  --hidden-import langgraph \
  --hidden-import deepagents \
  --hidden-import yaml \
  --hidden-import aiohttp \
  --hidden-import tree_sitter
```

## 🛠️ 技术栈

- **GUI 框架**: [Flet](https://flet.dev/) (基于 Flutter)
- **AI 框架**: [LangChain](https://langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/)
- **Agent 框架**: DashengAgent（自研，基于 LangGraph）
- **Prompt DSL**: 自研 YAML 模板引擎
- **代码分析**: Tree-sitter
- **网络请求**: aiohttp, requests, beautifulsoup4

## 📝 依赖列表

```
flet==0.82.2
langchain==1.2.12
langgraph==1.1.2
deepagents==0.4.10
PyYAML==6.0.3
aiohttp==3.13.3
requests==2.32.5
beautifulsoup4==4.14.3
lxml==6.0.2
tree-sitter==0.25.2
tree-sitter-python==0.25.0
tree-sitter-java==0.23.5
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

*最后更新: 2026-03-13*
## 📚 文档

- [Prompt DSL 架构](core/prompts/ARCHITECTURE.md) - 架构设计和最佳实践
- [Prompt DSL 使用指南](core/prompts/README.md) - 快速开始
- [工具系统调试](agent/README_TOOLS.md) - 工具调用问题排查
- [迁移指南](core/prompts/MIGRATION_GUIDE.md) - 从 Markdown 到 YAML

---

*最后更新：2026-03-16*
