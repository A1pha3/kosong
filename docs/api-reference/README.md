---
title: API 参考文档
description: Kosong API 完整参考文档索引
version: 0.23.0
last_updated: 2025-01-15
---

# API 参考文档

本节提供 Kosong 所有公开 API 的完整参考文档。每个模块都包含详细的函数签名、参数说明、返回值、异常处理和使用示例。

## 快速导航

### 核心函数

这些是 Kosong 最常用的核心函数：

- **[generate](./generate.md)** - 生成一条 LLM 响应消息
- **[step](./step.md)** - 执行一个完整的 Agent 步骤（包含工具调用处理）

### 消息模块

消息相关的类和类型定义：

- **[Message](./message.md)** - 消息类和内容片段（ContentPart、TextPart、ThinkPart、ImageURLPart、AudioURLPart、ToolCall、ToolCallPart）

### ChatProvider 模块

聊天提供者相关的协议和类：

- **[ChatProvider](./chat-provider.md)** - ChatProvider 协议、StreamedMessage 协议、TokenUsage 数据类和异常类型

### Tooling 模块

工具系统相关的类和协议：

- **[Tooling](./tooling.md)** - Tool、CallableTool、CallableTool2、ToolOk、ToolError、Toolset、SimpleToolset

## 按使用场景导航

### 我想生成 LLM 响应

1. 使用 [generate](./generate.md) 函数生成单条消息
2. 了解 [Message](./message.md) 结构来处理响应内容
3. 查看 [ChatProvider](./chat-provider.md) 了解如何配置不同的 LLM 服务

### 我想构建 AI Agent

1. 使用 [step](./step.md) 函数执行 Agent 步骤
2. 查看 [Tooling](./tooling.md) 了解如何创建和管理工具
3. 了解 [Message](./message.md) 中的 ToolCall 处理

### 我想实现自定义功能

1. 查看 [ChatProvider](./chat-provider.md) 协议实现自定义 LLM 提供者
2. 查看 [Tooling](./tooling.md) 中的 Toolset 协议实现自定义工具集
3. 了解 [Message](./message.md) 中的 ContentPart 扩展机制

## API 设计原则

Kosong 的 API 设计遵循以下原则：

1. **异步优先**：所有 I/O 操作都是异步的，使用 `async/await` 语法
2. **类型安全**：充分利用 Python 类型提示，支持静态类型检查
3. **流式处理**：支持实时流式接收和处理 LLM 响应
4. **协议导向**：使用 Protocol 定义接口，支持灵活的实现
5. **错误明确**：提供清晰的异常层次结构，便于错误处理

## 版本兼容性

本文档对应 Kosong v0.23.0 版本。API 可能在未来版本中发生变化，请关注 [CHANGELOG](../CHANGELOG.md) 了解最新变更。

## 相关资源

- [快速入门指南](../quick-start.md) - 快速上手 Kosong
- [核心概念](../core-concepts.md) - 理解 Kosong 的核心概念
- [实践指南](../guides/README.md) - 实际应用场景示例
- [架构设计](../architecture.md) - 深入了解内部实现

---

_文档版本: v0.23.0 | 最后更新: 2025-01-15_
