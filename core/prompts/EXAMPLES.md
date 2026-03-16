# PromptTemplate 使用示例

## 🎯 为什么使用 PromptTemplate？

`PromptTemplate` 不仅仅是一个数据容器，它提供了：
- ✅ **内置渲染引擎** - `render()` 方法处理所有变量替换
- ✅ **变量验证** - `validate()` 方法检查必填字段
- ✅ **类型安全** - dataclass 提供类型提示
- ✅ **可复用** - 模板对象可以多次渲染不同变量

## 📝 基础用法

### 1. 通过加载器获取模板对象

```python
from core.prompts import get_prompt_loader

loader = get_prompt_loader()

# 加载并渲染（简单用法）
role_prompt = loader.load_template("role")

# 获取模板对象（高级用法）
template_obj = loader.get_template_object("role")

# 使用模板对象渲染
rendered = template_obj.render()
```

### 2. 带变量渲染

```python
# 定义变量
variables = {
    "environment": "production",
    "user_name": "孙悟空",
    "features": ["功能 1", "功能 2", "功能 3"]
}

# 渲染模板
prompt = template_obj.render(**variables)
```

### 3. 多次渲染同一模板

```python
# 同一个模板对象可以多次渲染不同变量
dev_prompt = template_obj.render(environment="development")
prod_prompt = template_obj.render(environment="production")
```

## 🔧 高级功能

### 1. 直接创建 PromptTemplate

```python
from core.prompts import PromptTemplate

# 创建模板对象
template = PromptTemplate(
    module="greeting",
    pattern="你好，{{name}}！欢迎来到 {{environment}} 环境。",
    variables={"name": "用户", "environment": "开发"}
)

# 渲染
print(template.render(name="孙悟空"))
# 输出：你好，孙悟空！欢迎来到开发环境。
```

### 2. 变量验证

```python
template = PromptTemplate(
    module="email",
    pattern="收件人：{to}\n内容：{content}",
    variables={
        "to": ...,  # Ellipsis 表示必填
        "content": ...
    },
    validators=["no_empty_strings"]
)

# 验证变量
errors = template.validate(to="test@example.com", content="")
if errors:
    print(f"验证失败：{errors}")
    # 输出：验证失败：["Variable 'content' cannot be empty"]
```

### 3. 条件渲染

```python
template = PromptTemplate(
    module="conditional",
    pattern="""
基础内容

{%if ENABLE_DEBUG%}
调试模式开启！
调试信息：{{debug_info}}
{%endif%}
""",
    variables={"debug_info": "详细信息"}
)

# 不启用调试
print(template.render())
# 输出：基础内容

# 启用调试
print(template.render(ENABLE_DEBUG=True))
# 输出：基础内容\n\n调试模式开启！\n调试信息：详细信息
```

### 4. 循环渲染

```python
template = PromptTemplate(
    module="list",
    pattern="""
功能列表：
{%for feature in features%}
- {{feature}}
{%endfor%}
""",
    variables={"features": []}
)

# 渲染列表
print(template.render(features=["登录", "注册", "支付"]))
# 输出：
# 功能列表：
# - 登录
# - 注册
# - 支付
```

## 🎨 实际应用场景

### 场景 1：多环境部署

```python
from core.prompts import get_prompt_loader

loader = get_prompt_loader()
template = loader.get_template_object("role")

# 开发环境
dev_prompt = template.render(
    environment="development",
    ENABLE_DEBUG=True,
    debug_level="verbose"
)

# 生产环境
prod_prompt = template.render(
    environment="production",
    ENABLE_DEBUG=False
)
```

### 场景 2：个性化提示词

```python
template = loader.get_template_object("capabilities")

# 为不同用户生成个性化提示词
prompts = {
    "alice": template.render(
        user_name="Alice",
        preferred_language="Python",
        expertise_level="advanced"
    ),
    "bob": template.render(
        user_name="Bob",
        preferred_language="JavaScript",
        expertise_level="beginner"
    ),
}
```

### 场景 3：A/B 测试

```python
# 测试不同的提示词版本
template_v1 = PromptTemplate(
    module="test_v1",
    pattern="版本 1: {{message}}"
)

template_v2 = PromptTemplate(
    module="test_v2",
    pattern="版本 2: {{message}}"
)

# 对比效果
result_a = template_v1.render(message="你好")
result_b = template_v2.render(message="你好")
```

## 🧪 测试示例

```python
import unittest
from core.prompts import PromptTemplate

class TestPromptTemplate(unittest.TestCase):
    
    def test_basic_render(self):
        template = PromptTemplate(
            module="test",
            pattern="Hello, {{name}}!",
            variables={"name": "World"}
        )
        result = template.render()
        self.assertEqual(result, "Hello, World!")
    
    def test_variable_override(self):
        template = PromptTemplate(
            module="test",
            pattern="Hello, {{name}}!",
            variables={"name": "Default"}
        )
        result = template.render(name="Override")
        self.assertEqual(result, "Hello, Override!")
    
    def test_validation(self):
        template = PromptTemplate(
            module="test",
            pattern="{required}",
            variables={"required": ...}  # Ellipsis = required
        )
        errors = template.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("required", errors[0])

if __name__ == "__main__":
    unittest.main()
```

## 📊 性能对比

| 用法 | 场景 | 推荐度 |
|------|------|--------|
| `loader.load_template()` | 简单加载，一次性使用 | ⭐⭐⭐⭐ |
| `loader.get_template_object()` | 多次渲染，高级用法 | ⭐⭐⭐⭐⭐ |
| 直接创建 `PromptTemplate` | 动态模板，测试 | ⭐⭐⭐⭐ |

## 💡 最佳实践

1. **缓存模板对象** - 不要每次都重新加载，获取一次后重复使用
2. **使用变量验证** - 对必填字段使用 `...` (Ellipsis)
3. **分离配置和内容** - YAML 中定义结构，代码中提供变量
4. **单元测试** - 为关键模板编写测试用例

---

_有问题？找俺老孙！🐒_
