---
title: 流式输出指南
description: 学习如何使用 Kosong 实现流式输出，提供实时响应体验
version: 0.23.0
last_updated: 2025-01-15
---

# 流式输出指南

流式输出（Streaming）是现代 AI 应用的重要特性，它允许应用在 AI 生成内容的同时实时显示结果，而不是等待完整响应后才展示。这大大提升了用户体验，特别是在生成长文本时。

## 场景说明

流式输出适用于以下场景：

- **聊天应用**：逐字显示 AI 的回复，类似 ChatGPT 的打字效果
- **内容生成**：实时展示文章、代码或其他长文本的生成过程
- **实时反馈**：让用户知道系统正在工作，避免长时间等待的焦虑
- **工具调用监控**：实时显示 AI 正在调用哪些工具，提高透明度

## 流式输出的工作原理

在 Kosong 中，流式输出通过回调函数实现。当调用 `kosong.generate()` 时，可以传入两个可选的回调函数：

- `on_message_part`：每当接收到一个消息片段时调用
- `on_tool_call`：每当完成一个工具调用时调用

### 消息片段类型

流式输出中的消息片段（`StreamedMessagePart`）可以是以下类型之一：

- `TextPart`：文本内容片段
- `ThinkPart`：思考过程片段（如果模型支持）
- `ToolCall`：完整的工具调用
- `ToolCallPart`：工具调用参数的片段

Kosong 会自动将这些片段合并成完整的消息，你只需要在回调中处理每个片段即可。


## 基础示例：实时显示文本

以下是最简单的流式输出实现，逐字显示 AI 的响应：

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def main() -> None:
    # 初始化 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="请用 100 字介绍一下 Python 编程语言。"),
    ]

    # 定义回调函数处理每个消息片段
    def on_message_part(part: StreamedMessagePart) -> None:
        # 只处理文本片段
        if isinstance(part, TextPart):
            # 实时打印文本，不换行
            print(part.text, end="", flush=True)

    print("AI: ", end="", flush=True)
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一个专业的技术讲解员。",
        tools=[],
        history=history,
        on_message_part=on_message_part,  # 传入回调函数
    )
    
    print()  # 换行
    print(f"\n使用 Token: {result.usage.total if result.usage else 'N/A'}")


asyncio.run(main())
```

**运行说明**：

1. 将 `your_kimi_api_key_here` 替换为你的 Kimi API 密钥
2. 运行脚本：`python streaming_basic.py`
3. 观察文本如何逐字显示，而不是一次性出现

**预期输出**：

```
AI: Python 是一种高级、解释型、面向对象的编程语言...（逐字显示）

使用 Token: 150
```


## 处理不同类型的消息片段

在实际应用中，消息可能包含多种类型的内容。以下示例展示如何处理不同类型的片段：

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart, ThinkPart, ToolCall, ToolCallPart


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="解释一下量子计算的基本原理。"),
    ]

    def on_message_part(part: StreamedMessagePart) -> None:
        """处理不同类型的消息片段。"""
        match part:
            case TextPart():
                # 普通文本内容
                print(part.text, end="", flush=True)
            
            case ThinkPart():
                # 思考过程（某些模型支持）
                print(f"\n[思考中: {part.think}]", end="", flush=True)
            
            case ToolCall():
                # 完整的工具调用
                print(f"\n[调用工具: {part.function.name}]", end="", flush=True)
            
            case ToolCallPart():
                # 工具调用参数片段（通常不需要显示）
                pass

    print("AI: ", end="", flush=True)
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一个物理学专家。",
        tools=[],
        history=history,
        on_message_part=on_message_part,
    )
    
    print("\n")


asyncio.run(main())
```

**关键点**：

- 使用 `match` 语句（或 `isinstance`）区分不同类型的片段
- `TextPart` 是最常见的片段类型，包含实际的文本内容
- `ThinkPart` 包含模型的思考过程（需要模型支持）
- `ToolCall` 和 `ToolCallPart` 用于工具调用场景


## 异步回调函数

回调函数可以是同步的或异步的。如果需要在回调中执行异步操作（如写入数据库、发送网络请求），使用异步回调：

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="写一首关于春天的诗。"),
    ]

    # 异步回调函数
    async def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            # 模拟异步操作（如保存到数据库）
            await asyncio.sleep(0.01)  # 模拟 I/O 延迟
            print(part.text, end="", flush=True)

    print("AI: ", end="", flush=True)
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一位诗人。",
        tools=[],
        history=history,
        on_message_part=on_message_part,  # 异步回调
    )
    
    print("\n")


asyncio.run(main())
```

**注意事项**：

- Kosong 会自动检测回调函数是同步还是异步
- 异步回调允许你在处理片段时执行 I/O 操作
- 不要在回调中执行耗时的计算，这会阻塞流式输出


## 流式工具调用

当 AI 需要调用工具时，可以使用 `on_tool_call` 回调来实时监控工具调用：

```python
import asyncio

from pydantic import BaseModel

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart, ToolCall
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 定义一个天气查询工具
class WeatherParams(BaseModel):
    city: str


class WeatherTool(CallableTool2[WeatherParams]):
    name: str = "get_weather"
    description: str = "查询指定城市的天气信息。"
    params: type[WeatherParams] = WeatherParams

    async def __call__(self, params: WeatherParams) -> ToolReturnType:
        # 模拟天气查询
        await asyncio.sleep(0.5)
        return ToolOk(output=f"{params.city}的天气：晴天，温度 22°C")


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    toolset = SimpleToolset()
    toolset += WeatherTool()

    history = [
        Message(role="user", content="北京和上海的天气怎么样？"),
    ]

    # 处理消息片段
    def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            print(part.text, end="", flush=True)

    # 处理完整的工具调用
    def on_tool_call(tool_call: ToolCall) -> None:
        print(f"\n[正在调用工具: {tool_call.function.name}]", flush=True)
        print(f"[参数: {tool_call.function.arguments}]", flush=True)

    print("AI: ", end="", flush=True)
    
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个天气助手。",
        toolset=toolset,
        history=history,
        on_message_part=on_message_part,
        on_tool_call=on_tool_call,  # 工具调用回调
    )
    
    print("\n")
    
    # 显示工具执行结果
    tool_results = await result.tool_results()
    for tr in tool_results:
        print(f"[工具结果]: {tr.result.output}")


asyncio.run(main())
```

**预期输出**：

```
AI: 让我为你查询这两个城市的天气。
[正在调用工具: get_weather]
[参数: {"city": "北京"}]
[正在调用工具: get_weather]
[参数: {"city": "上海"}]

[工具结果]: 北京的天气：晴天，温度 22°C
[工具结果]: 上海的天气：晴天，温度 22°C
```

**关键点**：

- `on_tool_call` 在工具调用完整接收后触发
- 工具调用参数可能通过多个 `ToolCallPart` 片段逐步构建
- 使用 `kosong.step()` 而不是 `kosong.generate()` 来自动执行工具


## 构建交互式流式聊天应用

以下是一个完整的交互式聊天应用，结合了流式输出和多轮对话：

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def streaming_chat() -> None:
    """运行一个支持流式输出的交互式聊天应用。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    system_prompt = "你是一个友好、乐于助人的 AI 助手。"
    history: list[Message] = []

    print("流式聊天机器人已启动！输入 'exit' 退出。\n")

    while True:
        # 获取用户输入
        user_input = input("你: ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "退出"}:
            print("再见！")
            break

        # 添加用户消息到历史
        history.append(Message(role="user", content=user_input))

        # 定义流式输出回调
        def on_message_part(part: StreamedMessagePart) -> None:
            if isinstance(part, TextPart):
                print(part.text, end="", flush=True)

        try:
            print("AI: ", end="", flush=True)
            
            # 生成响应
            result = await kosong.generate(
                chat_provider=kimi,
                system_prompt=system_prompt,
                tools=[],
                history=history,
                on_message_part=on_message_part,
            )
            
            print("\n")  # 换行
            
            # 添加 AI 响应到历史
            history.append(result.message)

        except Exception as e:
            print(f"\n错误: {e}\n")
            # 发生错误时移除最后的用户消息
            history.pop()


asyncio.run(streaming_chat())
```

**运行说明**：

1. 替换 API 密钥
2. 运行脚本：`python streaming_chat.py`
3. 与 AI 对话，观察流式输出效果
4. 输入 `exit` 退出

**示例对话**：

```
你: 你好
AI: 你好！很高兴见到你。有什么我可以帮助你的吗？（逐字显示）

你: 给我讲个笑话
AI: 好的！为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25！（逐字显示）
```


## 错误处理和重试

在流式输出过程中可能会遇到各种错误。以下是处理这些错误的最佳实践：

### 1. 基础错误处理

```python
import asyncio

import kosong
from kosong.chat_provider import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    ChatProviderError,
    StreamedMessagePart,
)
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def safe_streaming_generate() -> None:
    """带错误处理的流式生成。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="介绍一下人工智能。"),
    ]

    def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            print(part.text, end="", flush=True)

    try:
        print("AI: ", end="", flush=True)
        
        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt="你是一个 AI 专家。",
            tools=[],
            history=history,
            on_message_part=on_message_part,
        )
        
        print("\n")

    except APIConnectionError as e:
        print(f"\n\n连接错误: 无法连接到 API 服务器。请检查网络连接。")
        print(f"详细信息: {e}")

    except APITimeoutError as e:
        print(f"\n\n超时错误: API 请求超时。请稍后重试。")
        print(f"详细信息: {e}")

    except APIStatusError as e:
        print(f"\n\nAPI 错误 (状态码 {e.status_code}): {e}")
        if e.status_code == 429:
            print("提示: 请求过于频繁，请稍后重试。")
        elif e.status_code >= 500:
            print("提示: 服务器错误，请稍后重试。")

    except ChatProviderError as e:
        print(f"\n\n聊天服务错误: {e}")

    except Exception as e:
        print(f"\n\n未知错误: {e}")


asyncio.run(safe_streaming_generate())
```


### 2. 自动重试机制

对于临时性错误（如网络波动、API 限流），可以实现自动重试：

```python
import asyncio
from typing import Any

import kosong
from kosong.chat_provider import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    StreamedMessagePart,
)
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def generate_with_retry(
    kimi: Kimi,
    system_prompt: str,
    history: list[Message],
    on_message_part: Any,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> kosong.GenerateResult | None:
    """带重试机制的生成函数。"""
    for attempt in range(max_retries):
        try:
            result = await kosong.generate(
                chat_provider=kimi,
                system_prompt=system_prompt,
                tools=[],
                history=history,
                on_message_part=on_message_part,
            )
            return result

        except (APIConnectionError, APITimeoutError) as e:
            if attempt < max_retries - 1:
                print(f"\n[重试 {attempt + 1}/{max_retries}]: {e}")
                await asyncio.sleep(retry_delay * (attempt + 1))  # 指数退避
            else:
                print(f"\n[失败]: 已达到最大重试次数。")
                raise

        except APIStatusError as e:
            # 对于 429 (限流) 和 5xx 错误重试
            if e.status_code == 429 or e.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    print(f"\n[重试 {attempt + 1}/{max_retries}]: 状态码 {e.status_code}，等待 {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"\n[失败]: 已达到最大重试次数。")
                    raise
            else:
                # 对于其他状态码（如 4xx），不重试
                raise

    return None


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="解释一下机器学习。"),
    ]

    def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            print(part.text, end="", flush=True)

    print("AI: ", end="", flush=True)
    
    try:
        result = await generate_with_retry(
            kimi=kimi,
            system_prompt="你是一个 AI 专家。",
            history=history,
            on_message_part=on_message_part,
            max_retries=3,
            retry_delay=1.0,
        )
        
        if result:
            print("\n")
            print(f"成功生成响应，使用 Token: {result.usage.total if result.usage else 'N/A'}")

    except Exception as e:
        print(f"\n最终失败: {e}")


asyncio.run(main())
```

**重试策略说明**：

- 对网络错误和超时错误自动重试
- 对 429（限流）和 5xx（服务器错误）重试
- 使用指数退避策略，避免过于频繁的重试
- 对 4xx 客户端错误（除 429 外）不重试，因为重试也会失败


### 3. 流式输出中断处理

在流式输出过程中，可能需要处理中断（如用户取消）：

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def cancellable_streaming() -> None:
    """支持取消的流式输出。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="写一篇 1000 字的文章介绍量子计算。"),
    ]

    def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            print(part.text, end="", flush=True)

    # 创建一个可以取消的任务
    async def generate_task():
        print("AI: ", end="", flush=True)
        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt="你是一个技术作家。",
            tools=[],
            history=history,
            on_message_part=on_message_part,
        )
        print("\n")
        return result

    task = asyncio.create_task(generate_task())

    try:
        # 设置超时时间（例如 30 秒）
        result = await asyncio.wait_for(task, timeout=30.0)
        print(f"完成！使用 Token: {result.usage.total if result.usage else 'N/A'}")

    except asyncio.TimeoutError:
        print("\n\n[超时]: 生成时间过长，已取消。")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("[已取消]: 任务已成功取消。")

    except KeyboardInterrupt:
        print("\n\n[中断]: 用户取消了操作。")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("[已取消]: 任务已成功取消。")


asyncio.run(cancellable_streaming())
```

**关键点**：

- 使用 `asyncio.create_task()` 创建可取消的任务
- 使用 `asyncio.wait_for()` 设置超时
- 捕获 `KeyboardInterrupt` 处理用户中断（Ctrl+C）
- 取消任务后需要 `await` 以确保清理完成


## 高级应用场景

### 1. 保存流式输出到文件

在生成内容的同时保存到文件：

```python
import asyncio
from pathlib import Path

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def stream_to_file() -> None:
    """将流式输出保存到文件。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="写一篇关于 Python 异步编程的教程。"),
    ]

    output_file = Path("output.txt")
    
    # 打开文件用于写入
    with output_file.open("w", encoding="utf-8") as f:
        def on_message_part(part: StreamedMessagePart) -> None:
            if isinstance(part, TextPart):
                # 同时显示和保存
                print(part.text, end="", flush=True)
                f.write(part.text)
                f.flush()  # 立即写入磁盘

        print("AI: ", end="", flush=True)
        
        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt="你是一个技术教程作者。",
            tools=[],
            history=history,
            on_message_part=on_message_part,
        )
        
        print("\n")
    
    print(f"内容已保存到 {output_file}")


asyncio.run(stream_to_file())
```

### 2. 实时统计和监控

在流式输出过程中收集统计信息：

```python
import asyncio
import time

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


class StreamingStats:
    """流式输出统计信息。"""

    def __init__(self):
        self.start_time = time.time()
        self.first_token_time: float | None = None
        self.char_count = 0
        self.token_count = 0

    def record_token(self, text: str) -> None:
        """记录一个 token。"""
        if self.first_token_time is None:
            self.first_token_time = time.time()
        self.char_count += len(text)
        self.token_count += 1

    def get_stats(self) -> dict[str, float]:
        """获取统计信息。"""
        total_time = time.time() - self.start_time
        ttft = (
            self.first_token_time - self.start_time
            if self.first_token_time
            else 0
        )
        tps = self.token_count / total_time if total_time > 0 else 0
        
        return {
            "total_time": total_time,
            "time_to_first_token": ttft,
            "tokens_per_second": tps,
            "char_count": self.char_count,
            "token_count": self.token_count,
        }


async def streaming_with_stats() -> None:
    """带统计信息的流式输出。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="介绍一下深度学习的发展历史。"),
    ]

    stats = StreamingStats()

    def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            stats.record_token(part.text)
            print(part.text, end="", flush=True)

    print("AI: ", end="", flush=True)
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一个 AI 历史学家。",
        tools=[],
        history=history,
        on_message_part=on_message_part,
    )
    
    print("\n")
    
    # 显示统计信息
    stats_data = stats.get_stats()
    print(f"\n--- 统计信息 ---")
    print(f"总耗时: {stats_data['total_time']:.2f}s")
    print(f"首 token 延迟: {stats_data['time_to_first_token']:.2f}s")
    print(f"生成速度: {stats_data['tokens_per_second']:.2f} tokens/s")
    print(f"字符数: {stats_data['char_count']}")
    print(f"Token 数: {stats_data['token_count']}")


asyncio.run(streaming_with_stats())
```

**预期输出**：

```
AI: 深度学习的发展可以追溯到...（流式显示）

--- 统计信息 ---
总耗时: 5.23s
首 token 延迟: 0.45s
生成速度: 28.5 tokens/s
字符数: 523
Token 数: 149
```


### 3. Web 应用中的流式输出

在 Web 应用中使用 Server-Sent Events (SSE) 实现流式输出：

```python
import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart

app = FastAPI()


async def generate_stream(user_message: str):
    """生成流式响应的异步生成器。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [Message(role="user", content=user_message)]

    # 使用队列在回调和生成器之间传递数据
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            await queue.put(part.text)

    # 在后台任务中生成响应
    async def generate_task():
        try:
            await kosong.generate(
                chat_provider=kimi,
                system_prompt="你是一个友好的助手。",
                tools=[],
                history=history,
                on_message_part=on_message_part,
            )
        finally:
            # 发送结束信号
            await queue.put(None)

    # 启动生成任务
    task = asyncio.create_task(generate_task())

    try:
        # 从队列中读取并发送数据
        while True:
            text = await queue.get()
            if text is None:
                break
            # 以 SSE 格式发送
            yield f"data: {json.dumps({'text': text})}\n\n"
    finally:
        # 确保任务完成
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


@app.get("/chat")
async def chat(message: str):
    """流式聊天端点。"""
    return StreamingResponse(
        generate_stream(message),
        media_type="text/event-stream",
    )


# 运行服务器：uvicorn streaming_web:app --reload
```

**客户端示例（JavaScript）**：

```javascript
const eventSource = new EventSource('/chat?message=你好');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    document.getElementById('output').textContent += data.text;
};

eventSource.onerror = () => {
    eventSource.close();
};
```


## 最佳实践

### 1. 选择合适的场景使用流式输出

**适合使用流式输出**：
- 生成长文本内容（文章、代码、解释等）
- 交互式聊天应用
- 需要实时反馈的场景
- 用户体验优先的应用

**不适合使用流式输出**：
- 批量处理任务
- 需要完整响应才能继续的场景
- 后台任务和定时任务
- 对延迟不敏感的场景

### 2. 优化用户体验

```python
import asyncio

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


async def optimized_streaming() -> None:
    """优化的流式输出体验。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="解释一下区块链技术。"),
    ]

    buffer = ""
    buffer_size = 5  # 缓冲 5 个字符后再显示

    def on_message_part(part: StreamedMessagePart) -> None:
        nonlocal buffer
        
        if isinstance(part, TextPart):
            buffer += part.text
            
            # 当缓冲区达到一定大小时才显示
            if len(buffer) >= buffer_size:
                print(buffer, end="", flush=True)
                buffer = ""

    print("AI: ", end="", flush=True)
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt="你是一个技术专家。",
        tools=[],
        history=history,
        on_message_part=on_message_part,
    )
    
    # 显示剩余的缓冲内容
    if buffer:
        print(buffer, end="", flush=True)
    
    print("\n")


asyncio.run(optimized_streaming())
```

**优化建议**：

- 使用缓冲减少频繁的 UI 更新
- 在首个 token 到达时显示加载指示器
- 提供取消按钮让用户可以中断生成
- 显示生成进度（如已生成字符数）

### 3. 处理并发请求

在多用户场景中，合理管理并发：

```python
import asyncio
from typing import Any

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart


class StreamingManager:
    """管理多个并发流式请求。"""

    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.kimi = Kimi(
            base_url="https://api.moonshot.ai/v1",
            api_key="your_kimi_api_key_here",
            model="kimi-k2-turbo-preview",
        )

    async def generate(
        self,
        user_id: str,
        message: str,
        on_message_part: Any,
    ) -> kosong.GenerateResult:
        """限制并发的生成方法。"""
        async with self.semaphore:
            print(f"[{user_id}] 开始生成...")
            
            history = [Message(role="user", content=message)]
            
            result = await kosong.generate(
                chat_provider=self.kimi,
                system_prompt="你是一个助手。",
                tools=[],
                history=history,
                on_message_part=on_message_part,
            )
            
            print(f"[{user_id}] 生成完成")
            return result


async def test_concurrent_streaming() -> None:
    """测试并发流式请求。"""
    manager = StreamingManager(max_concurrent=3)

    async def user_request(user_id: str, message: str):
        def on_part(part: StreamedMessagePart) -> None:
            if isinstance(part, TextPart):
                print(f"[{user_id}] {part.text}", end="", flush=True)

        await manager.generate(user_id, message, on_part)
        print(f"\n[{user_id}] 完成\n")

    # 模拟 5 个并发用户请求
    tasks = [
        user_request("用户1", "介绍 Python"),
        user_request("用户2", "介绍 JavaScript"),
        user_request("用户3", "介绍 Go"),
        user_request("用户4", "介绍 Rust"),
        user_request("用户5", "介绍 Java"),
    ]

    await asyncio.gather(*tasks)


asyncio.run(test_concurrent_streaming())
```

**并发管理要点**：

- 使用 `asyncio.Semaphore` 限制并发数量
- 避免同时发起过多请求导致 API 限流
- 为每个用户维护独立的会话状态
- 监控资源使用情况


### 4. 性能监控和调试

```python
import asyncio
import logging
from typing import Any

import kosong
from kosong.chat_provider import StreamedMessagePart
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, TextPart

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def monitored_streaming() -> None:
    """带监控的流式输出。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    history = [
        Message(role="user", content="介绍一下云计算。"),
    ]

    part_count = 0

    def on_message_part(part: StreamedMessagePart) -> None:
        nonlocal part_count
        part_count += 1
        
        if isinstance(part, TextPart):
            logger.debug(f"收到文本片段 #{part_count}: {len(part.text)} 字符")
            print(part.text, end="", flush=True)

    logger.info("开始生成响应")
    
    try:
        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt="你是一个云计算专家。",
            tools=[],
            history=history,
            on_message_part=on_message_part,
        )
        
        print("\n")
        
        logger.info(f"生成完成: 收到 {part_count} 个片段")
        if result.usage:
            logger.info(f"Token 使用: {result.usage.total}")

    except Exception as e:
        logger.error(f"生成失败: {e}", exc_info=True)
        raise


asyncio.run(monitored_streaming())
```

**监控建议**：

- 记录关键指标（延迟、吞吐量、错误率）
- 使用日志追踪问题
- 监控 API 配额使用情况
- 设置告警机制


## 常见问题

### Q: 流式输出和非流式输出有什么区别？

A: 主要区别在于用户体验和实现方式：

**流式输出**：
- 实时显示生成内容，用户体验更好
- 通过回调函数逐步接收内容
- 适合交互式应用和长文本生成
- 可以提前取消生成

**非流式输出**：
- 等待完整响应后一次性返回
- 实现更简单，代码更少
- 适合批量处理和后台任务
- 无法提前查看部分结果

### Q: 回调函数中可以执行什么操作？

A: 回调函数应该保持轻量级，避免阻塞：

**推荐操作**：
- 显示文本到控制台或 UI
- 写入文件或数据库（异步）
- 更新统计信息
- 发送到消息队列

**不推荐操作**：
- 耗时的计算任务
- 同步的网络请求
- 复杂的数据处理
- 阻塞式 I/O 操作

### Q: 如何处理流式输出中的乱码？

A: 确保正确处理字符编码：

```python
def on_message_part(part: StreamedMessagePart) -> None:
    if isinstance(part, TextPart):
        # 确保使用 UTF-8 编码
        print(part.text.encode('utf-8').decode('utf-8'), end="", flush=True)
```

对于文件写入，明确指定编码：

```python
with open("output.txt", "w", encoding="utf-8") as f:
    def on_message_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            f.write(part.text)
```

### Q: 流式输出会影响 Token 使用量吗？

A: 不会。流式输出和非流式输出使用相同数量的 Token，只是返回方式不同。

### Q: 如何在流式输出中实现打字机效果？

A: 可以在回调中添加延迟：

```python
import asyncio

async def on_message_part(part: StreamedMessagePart) -> None:
    if isinstance(part, TextPart):
        for char in part.text:
            print(char, end="", flush=True)
            await asyncio.sleep(0.05)  # 每个字符延迟 50ms
```

注意：这会显著增加总显示时间，仅用于演示效果。

### Q: 流式输出失败后如何恢复？

A: 流式输出失败通常无法从中断点恢复，需要重新生成：

```python
async def generate_with_fallback(kimi, history):
    try:
        # 尝试流式输出
        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt="你是一个助手。",
            tools=[],
            history=history,
            on_message_part=on_message_part,
        )
        return result
    except Exception as e:
        logger.warning(f"流式输出失败: {e}，尝试非流式模式")
        # 降级到非流式模式
        kimi_no_stream = kimi.with_generation_kwargs()
        kimi_no_stream.stream = False
        result = await kosong.generate(
            chat_provider=kimi_no_stream,
            system_prompt="你是一个助手。",
            tools=[],
            history=history,
        )
        return result
```

### Q: 如何测试流式输出功能？

A: 可以使用 Mock Provider 进行测试：

```python
from kosong.chat_provider.mock import Mock
from kosong.message import Message, TextPart

async def test_streaming():
    # Mock Provider 会立即返回预定义的响应
    mock = Mock(
        responses=[
            [TextPart(text="Hello"), TextPart(text=" "), TextPart(text="World")]
        ]
    )

    parts_received = []

    def on_message_part(part):
        parts_received.append(part)

    result = await kosong.generate(
        chat_provider=mock,
        system_prompt="",
        tools=[],
        history=[Message(role="user", content="Hi")],
        on_message_part=on_message_part,
    )

    assert len(parts_received) == 3
    assert result.message.content == "Hello World"
```


## 下一步

- 学习[多轮对话](./multi-turn-conversation.md)构建完整的聊天应用
- 学习[自定义工具](./custom-tools.md)扩展 AI 能力
- 学习[错误处理](./error-handling.md)提高应用稳定性
- 阅读[生产部署](./production-deployment.md)准备上线

## 相关资源

- [API 参考 - generate](../api-reference/generate.md)
- [API 参考 - step](../api-reference/step.md)
- [API 参考 - ChatProvider](../api-reference/chat-provider.md)
- [核心概念](../core-concepts.md)
