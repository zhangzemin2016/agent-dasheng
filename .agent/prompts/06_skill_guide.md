---
name: 技能创建指南
description: 指导用户创建自定义 Skill 的完整流程
priority: 50
enabled: true
---

# 用户对话创建技能

当用户说"帮我创建一个 xxx 技能"、"我想要一个能做 xxx 的 skill"等类似意图时：

## 1. 先和用户确认技能信息

需要确认：名称、功能描述、输入参数、执行命令

## 2. 拟定 SKILL.md 内容后直接调用 `create_skill` 工具

```python
create_skill(
    name="skill-name",
    description="技能功能描述",
    skill_md_content="完整的 SKILL.md 内容"
)
```

## 3. SKILL.md 模板格式

```markdown
---
name: skill-name
description: 技能描述
version: "1"
author: AI Agent
tags: [tag1, tag2]
inputs:
  param1: 参数1说明
  param2: 参数2说明
outputs:
  result: 执行结果
---

# skill-name

## 何时使用
描述这个 Skill 适合什么场景使用

## 功能
1. 功能点1
2. 功能点2

## 执行方式

```bash
python scripts/run.py --param1 "{param1}"
```

## 示例

```
/skill skill-name
/skill skill-name{param1:值1}
```
```

## 4. 脚本要求

- 脚本文件放在 `scripts/` 目录下
- 输出必须是 JSON 格式：`{"success": true, "output": "结果"}` 或 `{"success": false, "error": "错误信息"}`
- 使用 argparse 接收参数

## 5. 保存后告知用户

说明技能已创建，可通过 `/skill skill-name` 调用
