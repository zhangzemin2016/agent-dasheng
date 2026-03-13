# Agent Dasheng - AI Agent 桌面应用

基于 Flet、LangChain 和 DeepAgents 的智能 AI Agent 桌面应用，支持智能对话、技能扩展、项目管理和代码分析。

## ✨ 特性

- 🎨 **现代化 UI** - ChatGPT 风格深色主题，视觉舒适
- 💬 **智能对话** - 基于 LangGraph 的流式响应，实时显示 AI 回复
- 🔧 **技能系统** - 可扩展的技能体系，支持全局和项目级技能
- 📁 **项目管理** - 多项目管理，自动切换项目上下文
- 📜 **规则系统** - 支持内置、全局和项目三级规则配置
- 🛠️ **丰富工具** - 内置文件操作、代码分析、Git 操作、网络访问等工具
- 🧠 **DeepAgents 框架** - 深度集成 LangChain 与 LangGraph 的智能体构建框架

## 📁 项目结构

```
.
├── main.py                 # 应用主入口
├── llm_factory.py          # LLM 工厂，支持多模型提供商
├── agent/                  # Agent 系统
│   ├── deep_agent.py       # DeepAgent 封装，核心对话逻辑
│   ├── backends/           # 后端适配器
│   └── tools/              # Agent 工具集
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
│   └── skill_registry.py   # 技能注册表
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
- **Agent 框架**: [DeepAgents](https://github.com/langchain-ai/deepagents)
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