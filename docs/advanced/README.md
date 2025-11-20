# 高级主题

本节包含 Kosong 的高级主题文档，适合希望深入了解框架内部机制或扩展框架功能的开发者。

## 📚 主题列表

### [自定义 ChatProvider](./custom-chat-provider.md)

学习如何实现自定义的 ChatProvider，以支持新的 LLM 服务商或自定义的 API 接口。

**适合场景：**
- 需要集成 Kosong 尚未支持的 LLM 服务
- 需要在现有 Provider 基础上添加自定义逻辑
- 需要实现特殊的消息格式转换或错误处理

**主要内容：**
- ChatProvider 协议详解
- StreamedMessage 实现要求
- 消息格式转换策略
- 错误处理最佳实践
- 完整的自定义 Provider 示例

### [消息流处理机制](./message-streaming.md)

深入了解 Kosong 的流式消息处理机制，包括消息片段的合并算法和性能优化技巧。

**适合场景：**
- 需要优化流式处理性能
- 需要实现自定义的消息合并逻辑
- 需要理解 MergeableMixin 接口的工作原理

**主要内容：**
- 流式处理的设计原理
- MergeableMixin 接口详解
- 消息片段合并算法
- 性能优化技巧

### [异步工具执行](./async-tool-execution.md)

了解 Kosong 如何并发执行多个工具调用，以及如何实现自定义的 Toolset。

**适合场景：**
- 需要实现复杂的工具调度逻辑
- 需要优化工具执行性能
- 需要处理工具执行的取消和超时

**主要内容：**
- 工具并发执行机制
- ToolResultFuture 的使用
- 取消和超时处理
- 自定义 Toolset 实现

## 🎯 学习路径

如果你是第一次阅读高级主题文档，建议按以下顺序学习：

1. **自定义 ChatProvider** - 了解如何扩展 Kosong 支持新的 LLM 服务
2. **消息流处理机制** - 深入理解流式消息的处理原理
3. **异步工具执行** - 掌握工具并发执行的实现细节

## 📖 相关文档

- [架构设计](../architecture.md) - 了解 Kosong 的整体架构
- [API 参考](../api-reference/README.md) - 查阅详细的 API 文档
- [实践指南](../guides/README.md) - 学习常见场景的实现方法

## 💡 提示

高级主题文档假设你已经：
- 熟悉 Kosong 的基本用法
- 了解 Python 的异步编程（asyncio）
- 理解 Kosong 的核心概念（Message、ChatProvider、Tool 等）

如果你还不熟悉这些内容，建议先阅读：
- [快速入门](../quick-start.md)
- [核心概念](../core-concepts.md)
- [实践指南](../guides/README.md)
