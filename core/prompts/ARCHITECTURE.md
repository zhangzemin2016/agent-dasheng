# Prompt DSL 系统架构

## 📐 架构分层

```
┌─────────────────────────────────────────┐
│         PromptManager                   │  ← 统一入口（业务层）
│  - 整合 Loader + Registry + Skills      │
│  - 构建系统提示词                        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PromptRegistry                  │  ← 最上层（管理层）
│  - 注册和管理模板                        │
│  - 条件过滤、标签筛选                    │
│  - 不依赖 Loader 或 Template            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PromptLoader                    │  ← 中间层（加载层）
│  - 从 YAML 文件加载模板                  │
│  - 创建 PromptTemplate 对象              │
│  - 缓存管理                              │
│  - 不依赖 Registry                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PromptTemplate                  │  ← 最底层（渲染层）
│  - 存储模板内容和变量                    │
│  - 渲染模板（变量替换、条件、循环）      │
│  - 验证变量                              │
│  - 不依赖 Loader 或 Registry             │
└─────────────────────────────────────────┘
```

## 🎯 各层职责

### 1. PromptTemplate（最底层）

**文件**: `core/prompts/loader.py`

**职责**:
- ✅ 存储模板内容 (`pattern`) 和变量定义 (`variables`)
- ✅ 渲染模板（变量替换、条件块、循环块）
- ✅ 验证变量（必填字段、自定义规则）

**不负责**:
- ❌ 从文件加载（这是 Loader 的职责）
- ❌ 注册管理（这是 Registry 的职责）

**示例**:
```python
from core.prompts import PromptTemplate

template = PromptTemplate(
    module="greeting",
    pattern="Hello, {{name}}!",
    variables={"name": "World"}
)

# 渲染
result = template.render(name="孙悟空")
# 输出：Hello, 孙悟空!
```

### 2. PromptLoader（中间层）

**文件**: `core/prompts/loader.py`

**职责**:
- ✅ 从 YAML 文件读取配置和模板内容
- ✅ 创建 `PromptTemplate` 对象
- ✅ 检查加载条件（环境变量、特性开关）
- ✅ 缓存已加载的模板

**不负责**:
- ❌ 渲染模板（这是 Template 的职责）
- ❌ 注册管理（这是 Registry 的职责）

**示例**:
```python
from core.prompts import get_prompt_loader

loader = get_prompt_loader()

# 加载并渲染
role = loader.load_template("role", environment="prod")

# 获取模板对象（高级用法）
template_obj = loader.get_template_object("role")

# 获取配置
config = loader.get_config("role")
print(config.version)  # 输出：2.0
```

### 3. PromptRegistry（最上层）

**文件**: `core/prompts/prompt_registry.py`

**职责**:
- ✅ 注册和管理 `PromptTemplate` 对象
- ✅ 提供统一的访问接口
- ✅ 支持条件过滤和标签筛选
- ✅ 不依赖 Loader 或 Template（使用 `TYPE_CHECKING` 避免循环导入）

**不负责**:
- ❌ 从文件加载（这是 Loader 的职责）
- ❌ 渲染模板（这是 Template 的职责）

**示例**:
```python
from core.prompts import get_registry, get_prompt_loader

loader = get_prompt_loader()
registry = get_registry()

# 加载模板
loader.load_template("role")

# 注册到 Registry
config = loader.get_config("role")
template_obj = loader.get_template_object("role")
registry.register(config, template_obj)

# 通过 Registry 访问
rendered = registry.load("role", environment="prod")
```

### 4. PromptManager（统一入口）

**文件**: `core/prompt_manager.py`

**职责**:
- ✅ 整合 Loader + Registry + Skills
- ✅ 构建完整的系统提示词
- ✅ 对外提供统一的访问接口

**示例**:
```python
from core.prompt_manager import get_prompt_manager

manager = get_prompt_manager()

# 构建系统提示词
system_prompt = manager.build_system_prompt(
    environment="production"
)

# 获取模板对象（高级用法）
template_obj = manager.get_template_object("role")
```

## 🔄 依赖关系

```
PromptManager
    ↓
PromptRegistry ← （依赖，通过 TYPE_CHECKING 避免循环）
    ↓
PromptLoader
    ↓
PromptTemplate
```

**关键设计**:
- ✅ 下层不依赖上层（Template 不依赖 Loader，Loader 不依赖 Registry）
- ✅ Registry 使用 `TYPE_CHECKING` 避免与 Loader 的循环导入
- ✅ 每层职责清晰，单一职责原则

## 📊 对比：重构前后

### 重构前（混乱）

```
PromptLoader → PromptRegistry
    ↑              ↓
PromptTemplate ←───┘

问题：
- 循环依赖
- 职责不清
- 难以测试
```

### 重构后（清晰）

```
PromptManager
    ↓
PromptRegistry （不依赖下层）
    ↓
PromptLoader   （不依赖上层）
    ↓
PromptTemplate （最底层，独立）

优势：
- 无循环依赖
- 职责清晰
- 易于测试和维护
```

## 🧪 测试策略

### 单元测试

```python
import unittest
from core.prompts import PromptTemplate

class TestPromptTemplate(unittest.TestCase):
    def test_render(self):
        template = PromptTemplate(
            module="test",
            pattern="Hello, {{name}}!",
            variables={}
        )
        result = template.render(name="World")
        self.assertEqual(result, "Hello, World!")
```

### 集成测试

```python
from core.prompts import get_prompt_loader, get_registry

def test_full_flow():
    loader = get_prompt_loader()
    registry = get_registry()
    
    # 加载
    loader.load_template("role")
    
    # 注册
    config = loader.get_config("role")
    template = loader.get_template_object("role")
    registry.register(config, template)
    
    # 使用
    result = registry.load("role")
    assert result is not None
```

## 💡 最佳实践

1. **使用合适的层级**
   - 简单渲染 → 直接用 `PromptTemplate`
   - 从文件加载 → 用 `PromptLoader`
   - 统一管理 → 用 `PromptRegistry`
   - 完整功能 → 用 `PromptManager`

2. **避免循环导入**
   - 使用 `TYPE_CHECKING` 进行类型注解
   - 下层不导入上层

3. **缓存策略**
   - Loader 自动缓存已加载的模板
   - 开发时可用 `clear_cache()` 清空缓存

4. **错误处理**
   - 检查返回值是否为 `None`
   - 使用 `validate()` 验证变量

---

_架构清晰，代码才能长久！🐒_
