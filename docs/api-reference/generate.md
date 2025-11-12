---
title: kosong.generate
description: 生成一条 LLM 响应消息
version: 0.23.0
last_updated: 2025-01-15
---

# kosong.generate

> 生成一条 LLM 响应消息，支持流式处理和工具调用。

`generate()` 函数是 Kosong 的核心函数之一，用于从指定的 ChatProvider 生成一条完整的 LLM 响应消息。它会自动处理流式响应的合并，并通过回调函数实时通知消息片段和工具调用。

## 函数签名

```python
async def generate(
    chat_provider: ChatProvider,
    system_prompt: str,
    tools: Sequence[Tool],
    history: Sequence[Message],
    *,
    on_message_part: Callback[[StreamedMessagePart], None] | None = None,
    on_tool_call: Callback[[ToolCall], None] | None = None,
) -> GenerateResult:
    """
    Generate one message based on the given context.
    Parts of the message will be streamed to the specified callbacks if provided.
    """
    ...
```

## 参数说明

### 必需参数

- **chat_provider** (`ChatProvider`): 用于生成响应的聊天提供者实例，例如 `Kimi`、`Anthropic` 等
- **system_prompt** (`str`): 系统提示词，用于设定 AI 的角色和行为规范
- **tools** (`Sequence[Tool]`): 可供模型调用的工具列表，如果不需要工具调用可传入空列表
- **history** (`Sequence[Message]`): 对话历史消息列表，按时间顺序排列

### 可选参数

- **on_message_part** (`Callback[[StreamedMessagePart], None] | None`, 默认值: `None`): 
  流式消息片段回调函数。每当接收到一个消息片段时会被调用，可用于实时显示响应内容。回调函数可以是同步或异步函数。

- **on_tool_call** (`Callback[[ToolCall], None] | None`, 默认值: `None`): 
  工具调用回调函数。每当一个完整的工具调用被解析完成时会被调用。回调函数可以是同步或异步函数。

## 返回值

**类型：** `GenerateResult`

返回一个 `GenerateResult` 对象，包含以下字段：

- **id** (`str | None`): 生成消息的唯一标识符（如果 ChatProvider 提供）
- **message** (`Message`): 生成的完整消息对象，所有内容片段都已合并
- **usage** (`TokenUsage | None`): Token 使用统计信息（如果 ChatProvider 提供）

## 异常

- **APIConnectionError**: API 连接失败时抛出
- **APITimeoutError**: API 请求超时时抛出
- **APIStatusError**: API 返回 4xx 或 5xx 状态码时抛出
- **APIEmptyResponseError**: API 返回空响应时抛出
- **ChatProviderError**: 其他聊天提供者相关错误

## 使用示例

### 示例 1：基础对话生成

```python
# 基础对话生成示例

import asyncio
from kosong import generate
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message

async def main() -> None:
    # 创建 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    # 准备对话历史
    history = [
        Message(role="user", content="什么是 Python？"),
    ]
    
    # 生成响应
    result = await generate(
        chat_provider=kimi,
        system_prompt="你是一个专业的编程助手。",
        tools=[],
        history=history,
    )
    
    print(f"响应内容: {result.message.content}")
    print(f"Token 使用: {result.usage}")

asyncio.run(main())
```

**输出：**
```
响应内容: Python 是一种高级、解释型、通用的编程语言...
Token 使用: TokenUsage(input_other=25, output=150, input_cache_read=0, input_cache_creation=0)
```

### 示例 2：流式输出处理

```python
# 流式输出处理示例

import asyncio
from kosong import generate
from kosong.chat_provider.kimi import Kimi
from kosong.chat_provider import StreamedMessagePart
from kosong.message import Message, TextPart

async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    history = [
        Message(role="user", content="请写一首关于春天的诗。"),
    ]
    
    # 定义流式回调函数
    async def on_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            print(part.text, end="", flush=True)
    
    # 生成响应并实时显示
    result = await generate(
        chat_provider=kimi,
        system_prompt="你是一个诗人。",
        tools=[],
        history=history,
        on_message_part=on_part,
    )
    
    print("\n\n生成完成！")

asyncio.run(main())
```

### 示例 3：带工具调用的生成

```python
# 带工具调用的生成示例

import asyncio
from pydantic import BaseModel
from kosong import generate
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, ToolCall
from kosong.tooling import Tool

async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    # 定义工具
    class WeatherParams(BaseModel):
        city: str
    
    weather_tool = Tool(
        name="get_weather",
        description="获取指定城市的天气信息",
        params=WeatherParams,
    )
    
    history = [
        Message(role="user", content="北京今天天气怎么样？"),
    ]
    
    # 工具调用回调
    async def on_tool_call(tool_call: ToolCall) -> None:
        print(f"模型请求调用工具: {tool_call.name}")
        print(f"工具参数: {tool_call.params}")
    
    # 生成响应
    result = await generate(
        chat_provider=kimi,
        system_prompt="你是一个天气助手。",
        tools=[weather_tool],
        history=history,
        on_tool_call=on_tool_call,
    )
    
    # 检查是否有工具调用
    if result.message.tool_calls:
        print(f"生成了 {len(result.message.tool_calls)} 个工具调用")
        for tc in result.message.tool_calls:
            print(f"  - {tc.name}: {tc.params}")

asyncio.run(main())
```

### 示例 4：多轮对话

```python
# 多轮对话示例

import asyncio
from kosong import generate
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message

async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    # 初始化对话历史
    history: list[Message] = []
    
    # 第一轮对话
    history.append(Message(role="user", content="我叫小明"))
    result1 = await generate(
        chat_provider=kimi,
        system_prompt="你是一个友好的助手。",
        tools=[],
        history=history,
    )
    history.append(result1.message)
    print(f"助手: {result1.message.content}")
    
    # 第二轮对话
    history.append(Message(role="user", content="我叫什么名字？"))
    result2 = await generate(
        chat_provider=kimi,
        system_prompt="你是一个友好的助手。",
        tools=[],
        history=history,
    )
    history.append(result2.message)
    print(f"助手: {result2.message.content}")

asyncio.run(main())
```

**输出：**
```
助手: 你好，小明！很高兴认识你。
助手: 你叫小明。
```

## 注意事项

### 消息合并机制

`generate()` 函数会自动合并流式响应中的消息片段：

- 相邻的 `TextPart` 会被合并成一个
- 增量的 `ToolCall` 片段会被合并成完整的工具调用
- 只有完全合并后的消息才会被返回

### 回调函数执行

- 回调函数可以是同步函数或异步函数（使用 `async def` 定义）
- 回调函数中的异常不会中断生成过程，但会被记录
- `on_message_part` 接收的是原始流式片段的深拷贝，修改不会影响最终结果
- `on_tool_call` 只在工具调用完全解析完成后才会被调用

### 错误处理

建议使用 try-except 捕获可能的异常：

```python
from kosong.chat_provider import APIConnectionError, APITimeoutError

try:
    result = await generate(...)
except APIConnectionError as e:
    print(f"连接失败: {e}")
except APITimeoutError as e:
    print(f"请求超时: {e}")
```

### 性能考虑

- 使用 `on_message_part` 回调可以实现实时显示，提升用户体验
- 如果不需要实时处理，可以省略回调函数以减少开销
- 对于长对话历史，考虑定期清理或总结以控制 Token 消耗

## 相关 API

- [step](./step.md) - 在 `generate()` 基础上增加了工具执行功能
- [Message](./message.md) - 消息对象的详细说明
- [ChatProvider](./chat-provider.md) - ChatProvider 协议和实现
- [Tool](./tooling.md) - 工具定义和使用

## 与 step() 的区别

`generate()` 和 `step()` 的主要区别：

| 特性 | generate() | step() |
|------|-----------|--------|
| 工具调用 | 只生成工具调用请求 | 自动执行工具并返回结果 |
| 返回类型 | GenerateResult | StepResult |
| 使用场景 | 需要手动控制工具执行 | 自动化 Agent 流程 |
| 复杂度 | 较低，更灵活 | 较高，更便捷 |

---

_文档版本: v0.23.0 | 最后更新: 2025-01-15_
