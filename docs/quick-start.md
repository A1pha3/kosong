---
title: 快速入门指南
description: 帮助新用户在 30 分钟内完成 Kosong 的安装并运行第一个 AI Agent 应用
version: 0.23.0
last_updated: 2025-01-15
---

# 快速入门指南

欢迎使用 Kosong！本指南将帮助你在 30 分钟内完成安装并运行第一个 AI Agent 应用。

## 环境要求

在开始之前，请确保你的开发环境满足以下要求：

- **Python 3.13 或更高版本**：Kosong 需要 Python 3.13+ 的特性支持
- **uv 包管理器**：我们推荐使用 [uv](https://github.com/astral-sh/uv) 作为包管理器，它提供更快的依赖解析和安装速度

## 安装步骤

### 1. 初始化项目

使用 uv 创建一个新的 Python 项目：

```bash
uv init --python 3.13
```

### 2. 添加 Kosong 依赖

将 Kosong 添加到你的项目中：

```bash
uv add kosong
```

### 3. 准备 API 密钥

Kosong 支持多种 LLM 服务提供商。本指南使用 Kimi（月之暗面）作为示例。你需要：

- 访问 [Kimi 开放平台](https://platform.moonshot.cn/) 注册账号
- 获取你的 API 密钥

### 4. 设置环境变量（可选）

为了方便管理 API 密钥，你可以设置环境变量：

```bash
export KIMI_API_KEY="your_kimi_api_key_here"
```

### 5. 创建第一个脚本

创建一个名为 `main.py` 的文件，准备开始编写代码！

## 基础示例

### 示例 1：简单对话

这是最基础的使用方式，向 AI 发送一条消息并获取回复。

```python
import asyncio

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message


async def main() -> None:
    # 初始化 Kimi ChatProvider
    # base_url: Kimi API 的基础 URL
    # api_key: 你的 API 密钥
    # model: 使用的模型名称
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",  # 替换为你的 API 密钥
        model="kimi-k2-turbo-preview",
    )

    # 创建对话历史
    # Message 对象表示一条消息，包含角色（role）和内容（content）
    history = [
        Message(role="user", content="你好，请介绍一下你自己。"),
    ]

    # 调用 generate 函数生成回复
    # chat_provider: 使用的 LLM 服务提供商
    # system_prompt: 系统提示词，定义 AI 的行为
    # tools: 可用的工具列表（本例中为空）
    # history: 对话历史
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一个友好的助手。",
        tools=[],
        history=history,
    )
    
    # 打印 AI 的回复消息
    print("AI 回复：")
    print(result.message)
    
    # 打印 Token 使用情况
    print("\nToken 使用情况：")
    print(result.usage)


# 运行异步主函数
asyncio.run(main())
```

**运行示例：**

```bash
uv run python main.py
```

**预期输出：**

```
AI 回复：
Message(role='assistant', content=[TextPart(text='你好！我是 Kimi，一个由月之暗面科技开发的 AI 助手...')])

Token 使用情况：
TokenUsage(input_tokens=25, output_tokens=48)
```

### 示例 2：流式输出

流式输出允许你实时接收 AI 的回复内容，提供更好的用户体验。

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message


async def main() -> None:
    # 初始化 Kimi ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",  # 替换为你的 API 密钥
        model="kimi-k2-turbo-preview",
    )

    # 创建对话历史
    history = [
        Message(role="user", content="请用三句话介绍一下 Python 编程语言。"),
    ]

    # 定义流式输出回调函数
    # 每当接收到新的消息片段时，这个函数会被调用
    def output(message_part: StreamedMessagePart):
        # message_part 包含消息的增量内容
        print(message_part, end="", flush=True)

    # 调用 generate 函数，传入 on_message_part 回调
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一个简洁的技术讲解员。",
        tools=[],
        history=history,
        on_message_part=output,  # 设置流式输出回调
    )
    
    print("\n\n完整消息：")
    print(result.message)
    
    print("\nToken 使用情况：")
    print(result.usage)


# 运行异步主函数
asyncio.run(main())
```

**运行示例：**

```bash
uv run python main.py
```

**预期输出：**

你会看到 AI 的回复逐字显示，而不是等待全部生成完成后一次性输出：

```
Python 是一种高级编程语言...（逐字显示）

完整消息：
Message(role='assistant', content=[TextPart(text='Python 是一种高级编程语言...')])

Token 使用情况：
TokenUsage(input_tokens=30, output_tokens=52)
```

### 示例 3：工具调用

工具调用是 AI Agent 的核心能力，允许 AI 调用你定义的函数来完成特定任务。

```python
import asyncio

from pydantic import BaseModel

import kosong
from kosong import StepResult
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 定义工具参数的数据模型
# 使用 Pydantic BaseModel 进行参数验证
class AddToolParams(BaseModel):
    a: int  # 第一个整数
    b: int  # 第二个整数


# 定义一个加法工具
# 继承 CallableTool2 并指定参数类型
class AddTool(CallableTool2[AddToolParams]):
    name: str = "add"  # 工具名称
    description: str = "将两个整数相加。"  # 工具描述，AI 会根据这个描述决定何时使用
    params: type[AddToolParams] = AddToolParams  # 参数类型

    # 实现工具的执行逻辑
    async def __call__(self, params: AddToolParams) -> ToolReturnType:
        # 执行加法运算
        result = params.a + params.b
        # 返回 ToolOk 表示执行成功，output 是返回给 AI 的结果
        return ToolOk(output=f"计算结果：{params.a} + {params.b} = {result}")


async def main() -> None:
    # 初始化 Kimi ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",  # 替换为你的 API 密钥
        model="kimi-k2-turbo-preview",
    )

    # 创建工具集并添加工具
    # SimpleToolset 是 Kosong 提供的简单工具集实现
    toolset = SimpleToolset()
    toolset += AddTool()  # 将加法工具添加到工具集

    # 创建对话历史
    history = [
        Message(role="user", content="请使用 add 工具计算 123 加 456 的结果。"),
    ]

    # 使用 step 函数处理工具调用
    # step 会自动处理 AI 的工具调用请求，执行工具，并将结果返回给 AI
    result: StepResult = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个精确的数学助手。",
        toolset=toolset,  # 传入工具集
        history=history,
    )
    
    # 打印 AI 的回复消息
    print("AI 回复：")
    print(result.message)
    
    # 打印工具执行结果
    print("\n工具执行结果：")
    print(await result.tool_results())


# 运行异步主函数
asyncio.run(main())
```

**运行示例：**

```bash
uv run python main.py
```

**预期输出：**

在这个示例中，AI 会识别出需要使用 `add` 工具，调用它来计算 123 + 456，然后将结果整合到回复中：

```
AI 回复：
Message(role='assistant', content=[TextPart(text='好的，我来帮你计算。'), ToolCallPart(tool_call=ToolCall(id='call_123', name='add', arguments={'a': 123, 'b': 456}))])

工具执行结果：
[ToolResult(tool_call_id='call_123', output='计算结果：123 + 456 = 579')]
```

## 下一步学习

恭喜你完成了快速入门！现在你已经掌握了 Kosong 的基本用法。接下来，你可以：

### 深入理解核心概念

- [核心概念文档](./core-concepts.md)：深入了解 Message、ChatProvider、Tool、Toolset 等核心概念
- [架构设计文档](./architecture.md)：了解 Kosong 的整体架构和设计原理

### 学习实践指南

- [多轮对话指南](./guides/multi-turn-conversation.md)：学习如何构建支持多轮对话的聊天机器人
- [流式输出指南](./guides/streaming-output.md)：深入了解流式输出的工作原理和最佳实践
- [自定义工具指南](./guides/custom-tools.md)：学习如何创建更复杂的自定义工具
- [错误处理指南](./guides/error-handling.md)：了解如何优雅地处理各种错误情况
- [生产部署指南](./guides/production-deployment.md)：学习如何将应用部署到生产环境

### 查阅 API 参考

- [API 参考文档](./api-reference/README.md)：查阅完整的 API 文档，了解每个类和函数的详细用法

### 探索高级主题

- [自定义 ChatProvider](./advanced/custom-chat-provider.md)：学习如何实现自定义的 LLM 服务提供商
- [消息流处理机制](./advanced/message-streaming.md)：深入了解流式消息的处理机制
- [异步工具执行](./advanced/async-tool-execution.md)：了解工具的异步执行和并发处理

## 常见问题

### 如何使用其他 LLM 服务提供商？

Kosong 支持多种 LLM 服务提供商。除了 Kimi，你还可以使用：

- OpenAI（通过 `kosong.contrib.chat_provider.openai_legacy`）
- Anthropic（通过 `kosong.contrib.chat_provider.anthropic`）
- 或者实现自定义的 ChatProvider

详见 [自定义 ChatProvider 文档](./advanced/custom-chat-provider.md)。

### 如何管理对话历史？

在多轮对话中，你需要维护一个 `history` 列表，每次调用后将新的消息添加到历史中。详见 [多轮对话指南](./guides/multi-turn-conversation.md)。

### 工具调用失败怎么办？

工具可以返回 `ToolError` 来表示执行失败，AI 会根据错误信息调整策略。详见 [错误处理指南](./guides/error-handling.md)。

## 获取帮助

如果你遇到问题或有任何疑问：

- 查阅 [完整文档](./README.md)
- 访问 [GitHub Issues](https://github.com/your-repo/kosong/issues) 提交问题
- 加入我们的社区讨论

祝你使用 Kosong 构建出色的 AI Agent 应用！
