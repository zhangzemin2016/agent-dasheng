# 编程规范与架构原则

## 通用规范
- 代码结构清晰，命名规范（语义化、驼峰/下划线遵循语言惯例）
- 包含错误处理和边界情况
- 添加必要的注释说明（复杂逻辑必须注释）
- 如果是多文件项目，先创建目录结构

## 语言特定规范

### Python
- 严格遵循 PEP 8（缩进4空格、行长79/120字符、导入排序）
- 类型注解（Python 3.9+ 使用内置类型如 `list[str]`）
- 文档字符串使用 Google Style 或 NumPy Style
- 异步代码使用 `async/await`，避免回调地狱

### TypeScript/JavaScript
- 严格模式 `strict: true`，避免 `any` 类型
- 优先使用 `const`/`let`，避免 `var`
- 异步优先使用 `async/await`，合理使用 Promise
- Vue3 使用 Composition API + `<script setup>` 语法

### Java
- 遵循阿里巴巴 Java 开发手册
- 类名大驼峰、方法名小驼峰、常量全大写下划线
- 优先使用 `Optional` 避免 NPE，Stream API 处理集合
- Spring Boot 项目遵循分层架构（Controller-Service-Repository）

### Go
- 遵循 Effective Go 和 Uber Go Style Guide
- 错误处理显式检查 `if err != nil`，不忽略错误
- 接口设计遵循小接口原则，组合优于继承
- 并发使用 Goroutine + Channel，避免共享内存

### Rust
- 遵循 Rust API Guidelines，善用 Clippy 检查
- 所有权、借用、生命周期正确运用
- 错误处理使用 `Result<T, E>`，避免 `unwrap()` 生产代码
- 零成本抽象， unsafe 代码必须封装并注释原因

## 架构设计原则

- **单一职责**：每个模块/类/函数只做一件事
- **开闭原则**：对扩展开放，对修改关闭
- **依赖倒置**：依赖抽象接口，而非具体实现
- **DRY原则**：不重复自己，提取公共逻辑
- **KISS原则**：保持简单，避免过度设计

请专业、高效地帮助用户完成编程任务。
