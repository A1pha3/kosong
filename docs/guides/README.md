---
title: 实践指南
description: Kosong 实践指南索引
version: 0.23.0
last_updated: 2025-01-15
---

# 实践指南

本节提供 Kosong 在实际项目中的使用指南和最佳实践。每个指南都包含完整的代码示例、运行说明和常见问题解决方案。

## 指南列表

### [多轮对话](./multi-turn-conversation.md)

学习如何构建支持多轮对话的 AI 应用。本指南涵盖：

- 维护对话历史的基本方法
- 上下文管理策略
- 对话状态持久化
- 完整的聊天机器人实现示例

**适用场景**：聊天机器人、对话式 AI 助手、客服系统

### [流式输出](./streaming-output.md)

学习如何实现流式输出以提供更好的用户体验。本指南涵盖：

- 流式输出的工作原理
- 实时显示响应内容
- 处理流式工具调用
- 错误处理和重试策略

**适用场景**：实时聊天应用、交互式命令行工具、Web 应用

### [自定义工具](./custom-tools.md)

学习如何创建和使用自定义工具来扩展 AI Agent 的能力。本指南涵盖：

- 创建简单工具（使用 CallableTool2）
- 工具参数验证
- 工具错误处理
- 异步工具实现
- 工具组合和复用

**适用场景**：需要调用外部 API、数据库操作、文件处理的 AI 应用

### [错误处理](./error-handling.md)

学习如何正确处理 Kosong 应用中的各种错误。本指南涵盖：

- 常见异常类型及其处理方法
- API 错误处理
- 工具执行错误处理
- 重试策略
- 优雅降级

**适用场景**：生产环境应用、需要高可靠性的系统

### [生产部署](./production-deployment.md)

学习如何将 Kosong 应用部署到生产环境。本指南涵盖：

- 性能优化建议
- 并发处理策略
- 日志和监控配置
- API 密钥管理
- 成本控制

**适用场景**：准备上线的应用、需要优化性能的系统

## 学习路径建议

### 初学者路径

1. 先阅读[快速入门](../quick-start.md)了解基础用法
2. 学习[多轮对话](./multi-turn-conversation.md)构建第一个聊天应用
3. 学习[自定义工具](./custom-tools.md)扩展 Agent 能力
4. 学习[错误处理](./error-handling.md)提高应用稳定性

### 进阶路径

1. 学习[流式输出](./streaming-output.md)优化用户体验
2. 学习[生产部署](./production-deployment.md)准备上线
3. 阅读[架构设计](../architecture.md)深入了解内部实现
4. 阅读[高级主题](../advanced/README.md)掌握高级技巧

## 相关资源

- [API 参考](../api-reference/README.md) - 查阅详细的 API 文档
- [核心概念](../core-concepts.md) - 理解 Kosong 的核心概念
- [架构设计](../architecture.md) - 了解 Kosong 的设计原理
- [高级主题](../advanced/README.md) - 探索高级用法和扩展

## 贡献指南

如果你有好的实践经验想要分享，欢迎贡献新的指南！请参考[贡献指南](../contributing.md)了解如何提交。
