# 高级主题

本目录包含 Kosong 的深入技术细节和扩展指导，适合需要深度定制或贡献代码的高级用户。

## 🔬 主题列表

### [自定义 ChatProvider](./custom-chat-provider.md)
深入了解 ChatProvider 协议，学习如何实现自定义的聊天提供者以支持新的 LLM 服务。

**内容包括：**
- ChatProvider 协议详解
- StreamedMessage 实现要求
- 消息格式转换
- 错误处理实现
- 完整的自定义 Provider 示例

### [消息流处理](./message-streaming.md)
探索流式处理的设计原理和实现细节，掌握消息片段合并算法和性能优化技巧。

**内容包括：**
- 流式处理的设计原理
- MergeableMixin 接口详解
- 消息片段的合并算法
- 性能优化技巧

### [异步工具执行](./async-tool-execution.md)
深入理解工具并发执行机制，学习如何实现自定义 Toolset 和处理复杂的异步场景。

**内容包括：**
- 工具并发执行机制
- ToolResultFuture 的使用
- 取消和超时处理
- 自定义 Toolset 实现示例

## 🎓 前置知识

阅读这些高级主题前，建议先完成：

1. [快速入门指南](../quick-start.md)
2. [核心概念](../core-concepts.md)
3. [架构设计文档](../architecture.md)
4. 相关的[实践指南](../guides/README.md)

## 🔗 相关资源

- [架构设计文档](../architecture.md) - 了解整体架构
- [API 参考文档](../api-reference/README.md) - 查阅详细 API
- [贡献指南](../contributing.md) - 参与项目开发

---

_文档版本: v0.23.0 | 最后更新: 2025-01-15_
