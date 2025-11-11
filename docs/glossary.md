---
title: 术语翻译对照表
description: Kosong 文档中使用的技术术语中英文对照
version: 0.23.0
last_updated: 2025-01-15
---

# 术语翻译对照表

本文档列出了 Kosong 文档中使用的所有技术术语的中英文对照，以确保翻译的一致性。

## 核心概念

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| Chat Provider | 聊天提供者 | 提供 LLM 服务的抽象接口 |
| Message | 消息 | 对话中的一条消息 |
| Tool | 工具 | AI Agent 可以调用的功能 |
| Toolset | 工具集 | 管理多个工具的容器 |
| Streaming | 流式处理 | 实时接收和处理响应 |
| Content Part | 内容片段 | 消息内容的组成部分 |
| Tool Call | 工具调用 | AI 请求调用工具的指令 |
| Token Usage | Token 用量 | API 调用的 token 消耗统计 |

## 编程概念

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| Async | 异步 | 异步编程模式 |
| Future | Future 对象 | 异步操作的结果占位符 |
| Callback | 回调 | 异步操作完成时调用的函数 |
| Protocol | 协议 | Python 中的结构化类型定义 |
| Abstract Class | 抽象类 | 定义接口的基类 |
| Mixin | 混入类 | 提供可复用功能的类 |
| Type Hint | 类型注解 | Python 的类型标注 |

## 消息相关

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| Text Part | 文本片段 | 包含文本内容的消息片段 |
| Think Part | 思考片段 | 包含 AI 思考过程的消息片段 |
| Image URL Part | 图片 URL 片段 | 包含图片链接的消息片段 |
| Audio URL Part | 音频 URL 片段 | 包含音频链接的消息片段 |
| Tool Call Part | 工具调用片段 | 包含工具调用信息的消息片段 |
| Streamed Message | 流式消息 | 流式传输的消息对象 |
| Mergeable | 可合并的 | 支持增量合并的对象 |

## 工具相关

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| Callable Tool | 可调用工具 | 可以被执行的工具基类 |
| Tool Result | 工具结果 | 工具执行的返回结果 |
| Tool Error | 工具错误 | 工具执行失败的错误信息 |
| Tool Ok | 工具成功 | 工具执行成功的结果 |
| Tool Result Future | 工具结果 Future | 异步工具执行的 Future 对象 |
| Simple Toolset | 简单工具集 | 内置的基础工具集实现 |

## 错误和异常

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| API Connection Error | API 连接错误 | 无法连接到 API 服务 |
| API Timeout Error | API 超时错误 | API 请求超时 |
| API Status Error | API 状态错误 | API 返回错误状态码 |
| API Response Error | API 响应错误 | API 响应格式错误 |
| Tool Execution Error | 工具执行错误 | 工具执行过程中的错误 |

## 其他术语

| 英文术语 | 中文翻译 | 说明 |
|---------|---------|------|
| Agent | Agent / 智能体 | AI 代理程序 |
| LLM | 大语言模型 | Large Language Model |
| API Key | API 密钥 | 访问 API 服务的密钥 |
| Prompt | 提示词 | 发送给 LLM 的输入文本 |
| Response | 响应 | LLM 返回的输出 |
| Context | 上下文 | 对话的历史信息 |
| Conversation | 对话 | 多轮交互的会话 |
| Turn | 轮次 | 对话中的一次交互 |

## 使用规范

### 1. 术语首次出现

技术术语首次出现时，应提供英文原文：

```markdown
Kosong 使用 ChatProvider（聊天提供者）来抽象不同的 LLM 服务。
```

### 2. 后续使用

后续使用时，直接使用中文翻译：

```markdown
你可以实现自定义的聊天提供者来支持新的 LLM 服务。
```

### 3. 代码中的术语

代码中的类名、函数名等保持英文不变：

```python
from kosong import ChatProvider, Message

class MyProvider(ChatProvider):
    ...
```

### 4. 特殊情况

某些术语在技术社区中通常使用英文，可以保持英文或使用英文/中文混合：

- LLM（大语言模型）
- API（应用程序接口）
- Token（令牌）
- Agent（智能体）

## 更新记录

- 2025-01-15: 初始版本，包含核心术语

---

如果您发现术语翻译不一致或有更好的翻译建议，欢迎通过 [GitHub Issues](https://github.com/yourusername/kosong/issues) 反馈。
