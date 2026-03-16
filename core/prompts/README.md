# Prompt DSL System - 提示词管理系统

## 📖 概述

将提示词从 Markdown 迁移到 YAML DSL，支持：
- ✅ 版本控制（Git diff 更清晰）
- ✅ 条件加载（环境变量、特性开关）
- ✅ 变量插值（动态内容）
- ✅ 模板复用（减少重复）
- ✅ 调试追踪（影响分析）

## 🚀 快速开始

### 1. 加载提示词

```python
from core.prompts import PromptLoader

# 初始化加载器
loader = PromptLoader(templates_dir="core/prompts/templates")

# 加载单个模板（支持动态变量）
role_prompt = loader.load_template(
    "role",
    environment="production",
    user_preferences="简洁模式"
)

# 加载所有模板
loader.reload_all()
```

### 2. 在代码中使用

```python
from core.prompts import get_prompt_loader

# 获取全局加载器
prompt_loader = get_prompt_loader()

# 组合多个提示词
system_prompt = f"""
{prompt_loader.load_template("role")}

{prompt_loader.load_template("capabilities")}

{prompt_loader.load_template("tools")}
"""
```

## 📝 YAML 模板语法

### 基本结构

```yaml
config:
  name: role
  version: "2.0"
  description: 角色定义
  tags:
    - core
    - system

template: |
  # 提示词内容
  支持 Markdown 格式
  ...
```

### 变量替换

```yaml
template: |
  当前环境：{{environment}}
  用户：{{user_name}}
```

```python
loader.load_template("example", environment="prod", user_name="孙悟空")
```

### 环境变量

```yaml
template: |
  API 地址：${API_URL}
  调试模式：{%DEBUG_MODE%}
```

### 条件块

```yaml
template: |
  # 基础内容
  
  {%if ENABLE_ADVANCED%}
  ## 高级功能
  这里的内容只在 ENABLE_ADVANCED=1 时显示
  {%endif%}
```

### 循环块

```yaml
template: |
  ## 功能列表
  
  {%for feature in features%}
  - {{feature}}
  {%endfor%}
```

```python
loader.load_template("example", features=["功能 1", "功能 2", "功能 3"])
```

## 📂 目录结构

```
core/prompts/
├── __init__.py              # 模块导出
├── loader.py                # 加载器核心
├── prompt_registry.py       # 注册表
├── README.md                # 本文档
└── templates/               # YAML 模板
    ├── role.yaml
    ├── capabilities.yaml
    ├── tools.yaml
    └── task_strategy.yaml
```

## 🎯 最佳实践

### 1. 版本管理

- 每次修改更新 `config.version`
- 使用 Git 标签标记重要版本
- 在 `config.description` 说明变更内容

### 2. 条件加载

```yaml
conditions:
  env:
    ENV: production  # 只在生产环境加载
  features:
    - advanced_mode  # 需要 FEATURE_ADVANCED_MODE=1
```

### 3. 变量命名

- 使用 `snake_case` 或 `UPPER_CASE`
- 避免使用保留字（如 `if`, `for`）
- 在文档中说明所有可用变量

### 4. 性能优化

- 启用缓存（默认开启）
- 大批量加载使用 `reload_all()`
- 开发环境可设置 `PROMPT_CACHE=false` 禁用缓存

## 🔄 迁移指南

### 从 Markdown 迁移

1. 创建 YAML 文件，复制 MD 内容到 `template:` 字段
2. 添加 `config:` 元数据
3. 提取可变部分为变量 `{{variable}}`
4. 测试加载：`loader.load_template("name")`
5. 更新代码引用

### 兼容性

- 旧的 `.md` 文件暂时保留
- 新代码使用 DSL 加载器
- 逐步迁移所有引用

## 🧪 测试示例

```python
import unittest
from core.prompts import PromptLoader

class TestPromptLoader(unittest.TestCase):
    def test_load_role(self):
        loader = PromptLoader()
        role = loader.load_template("role")
        self.assertIn("智能助手", role)
    
    def test_variables(self):
        loader = PromptLoader()
        result = loader.load_template("example", name="孙悟空")
        self.assertIn("孙悟空", result)
```

## 📊 对比：MD vs DSL

| 特性 | Markdown | YAML DSL |
|------|----------|----------|
| 版本审查 | ❌ 纯文本 | ✅ 结构化 |
| 变量替换 | ❌ 不支持 | ✅ 原生支持 |
| 条件加载 | ❌ 需手写代码 | ✅ 配置化 |
| 调试追踪 | ❌ 无 | ✅ 注册表 |
| 复用性 | ❌ 低 | ✅ 高 |

---

_有问题？找俺老孙！🐒_
