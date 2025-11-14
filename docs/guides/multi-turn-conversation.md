---
title: 多轮对话指南
description: 学习如何使用 Kosong 构建支持多轮对话的 AI 应用
version: 0.23.0
last_updated: 2025-01-15
---

# 多轮对话指南

多轮对话是 AI 应用的核心功能之一。本指南将介绍如何使用 Kosong 构建支持多轮对话的应用，包括对话历史管理、上下文维护和状态持久化。

## 场景说明

多轮对话允许 AI 记住之前的交互内容，从而提供更连贯、更智能的响应。典型应用场景包括：

- **聊天机器人**：与用户进行自然的多轮交互
- **客服系统**：记住用户问题的上下文，提供更准确的帮助
- **对话式 AI 助手**：执行需要多步骤确认的复杂任务
- **教育应用**：根据学生的学习历史提供个性化指导

## 核心概念

在 Kosong 中，多轮对话通过维护一个 `Message` 列表来实现。每次调用 `kosong.generate()` 或 `kosong.step()` 时，都需要传入完整的对话历史：

```python
history: list[Message] = []

# 第一轮对话
history.append(Message(role="user", content="你好"))
result = await kosong.generate(chat_provider, system_prompt, tools, history)
history.append(result.message)

# 第二轮对话
history.append(Message(role="user", content="我叫小明"))
result = await kosong.generate(chat_provider, system_prompt, tools, history)
history.append(result.message)

# 第三轮对话
history.append(Message(role="user", content="我叫什么名字？"))
result = await kosong.generate(chat_provider, system_prompt, tools, history)
# AI 能够回答"小明"，因为它记住了之前的对话
```

## 基础示例：简单的多轮对话

以下是一个最简单的多轮对话实现：

```python
import asyncio

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message


async def main() -> None:
    # 初始化 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    system_prompt = "你是一个友好的助手。"
    history: list[Message] = []

    # 第一轮对话
    print("用户: 你好，我是小明")
    history.append(Message(role="user", content="你好，我是小明"))
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt=system_prompt,
        tools=[],
        history=history,
    )
    
    history.append(result.message)
    print(f"助手: {result.message.content}")

    # 第二轮对话
    print("\n用户: 我叫什么名字？")
    history.append(Message(role="user", content="我叫什么名字？"))
    
    result = await kosong.generate(
        chat_provider=kimi,
        system_prompt=system_prompt,
        tools=[],
        history=history,
    )
    
    history.append(result.message)
    print(f"助手: {result.message.content}")
    # 预期输出：助手能够回答"你叫小明"


asyncio.run(main())
```

**运行说明**：

1. 将 `your_kimi_api_key_here` 替换为你的 Kimi API 密钥
2. 运行脚本：`python multi_turn_basic.py`
3. 观察 AI 如何记住之前对话中的信息

## 交互式聊天机器人

下面是一个完整的交互式聊天机器人实现，支持用户输入和连续对话：

```python
import asyncio

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message


async def chat_loop() -> None:
    """运行一个交互式聊天循环。"""
    # 初始化 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    system_prompt = "你是一个友好、乐于助人的 AI 助手。"
    history: list[Message] = []

    print("聊天机器人已启动！输入 'exit' 或 'quit' 退出。\n")

    while True:
        # 获取用户输入
        user_input = input("你: ").strip()
        
        # 检查退出命令
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "退出"}:
            print("再见！")
            break

        # 将用户消息添加到历史
        history.append(Message(role="user", content=user_input))

        try:
            # 生成 AI 响应
            result = await kosong.generate(
                chat_provider=kimi,
                system_prompt=system_prompt,
                tools=[],
                history=history,
            )

            # 将 AI 响应添加到历史
            history.append(result.message)

            # 显示 AI 响应
            print(f"助手: {result.message.content}\n")

        except Exception as e:
            print(f"错误: {e}\n")
            # 发生错误时，移除最后添加的用户消息
            history.pop()


asyncio.run(chat_loop())
```

**运行说明**：

1. 替换 API 密钥
2. 运行脚本：`python chatbot.py`
3. 开始与 AI 对话，它会记住整个对话历史
4. 输入 `exit` 退出

**示例对话**：

```
你: 你好，我是一名 Python 开发者
助手: 你好！很高兴认识你。作为 Python 开发者，你一定对编程充满热情...

你: 我最近在学习异步编程
助手: 太好了！异步编程是 Python 的强大特性...

你: 我之前说我是做什么的？
助手: 你之前说你是一名 Python 开发者。
```

## 带工具调用的多轮对话

当使用 `kosong.step()` 进行工具调用时，需要将工具调用和工具结果也添加到对话历史中：

```python
import asyncio

from pydantic import BaseModel

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import ContentPart, Message, TextPart
from kosong.tooling import CallableTool2, ToolOk, ToolResult, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 定义一个简单的计算器工具
class CalculatorParams(BaseModel):
    expression: str


class CalculatorTool(CallableTool2[CalculatorParams]):
    name: str = "calculator"
    description: str = "计算数学表达式的结果。"
    params: type[CalculatorParams] = CalculatorParams

    async def __call__(self, params: CalculatorParams) -> ToolReturnType:
        try:
            # 注意：在生产环境中应该使用更安全的表达式求值方法
            result = eval(params.expression)
            return ToolOk(output=f"计算结果: {result}")
        except Exception as e:
            return ToolOk(output=f"计算错误: {str(e)}")


def tool_result_to_message(result: ToolResult) -> Message:
    """将工具结果转换为消息。"""
    match result.result.output:
        case str():
            content = result.result.output
        case ContentPart() as part:
            content = [part]
        case _:
            content = list(result.result.output)
    return Message(role="tool", tool_call_id=result.tool_call_id, content=content)


def extract_text(message: Message) -> str:
    """从消息中提取文本内容。"""
    if isinstance(message.content, str):
        return message.content
    return "".join(part.text for part in message.content if isinstance(part, TextPart))


async def chat_with_tools() -> None:
    """运行带工具调用的聊天循环。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    # 设置工具集
    toolset = SimpleToolset()
    toolset += CalculatorTool()

    system_prompt = "你是一个数学助手，可以使用计算器工具帮助用户进行计算。"
    history: list[Message] = []

    print("数学助手已启动！输入 'exit' 退出。\n")

    while True:
        user_input = input("你: ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "退出"}:
            print("再见！")
            break

        history.append(Message(role="user", content=user_input))

        # 可能需要多轮工具调用
        while True:
            result = await kosong.step(
                chat_provider=kimi,
                system_prompt=system_prompt,
                toolset=toolset,
                history=history,
            )

            # 获取工具结果
            tool_results = await result.tool_results()
            tool_messages = [tool_result_to_message(tr) for tr in tool_results]

            # 显示助手响应
            if text := extract_text(result.message):
                print(f"助手: {text}")

            # 显示工具执行结果（可选）
            for tool_msg in tool_messages:
                if text := extract_text(tool_msg):
                    print(f"[工具执行]: {text}")

            # 如果没有工具调用，结束本轮对话
            if not result.tool_calls:
                break

            # 将助手消息和工具结果添加到历史
            history.append(result.message)
            history.extend(tool_messages)

        print()


asyncio.run(chat_with_tools())
```

**运行说明**：

1. 替换 API 密钥
2. 运行脚本：`python chatbot_with_tools.py`
3. 尝试让 AI 进行计算，例如："帮我算一下 123 * 456"

**示例对话**：

```
你: 帮我算一下 100 + 200
[工具执行]: 计算结果: 300
助手: 100 + 200 的结果是 300。

你: 再乘以 2 呢？
[工具执行]: 计算结果: 600
助手: 300 乘以 2 的结果是 600。
```

## 上下文管理策略

### 1. 限制历史长度

对话历史过长会导致 token 消耗增加和响应变慢。可以通过限制历史消息数量来控制：

```python
MAX_HISTORY_LENGTH = 20  # 保留最近 20 条消息

def trim_history(history: list[Message], max_length: int) -> list[Message]:
    """保留最近的消息，但始终保留系统消息。"""
    if len(history) <= max_length:
        return history
    
    # 分离系统消息和其他消息
    system_messages = [msg for msg in history if msg.role == "system"]
    other_messages = [msg for msg in history if msg.role != "system"]
    
    # 保留最近的消息
    recent_messages = other_messages[-max_length:]
    
    # 合并系统消息和最近消息
    return system_messages + recent_messages


# 使用示例
history.append(Message(role="user", content=user_input))
history = trim_history(history, MAX_HISTORY_LENGTH)

result = await kosong.generate(
    chat_provider=kimi,
    system_prompt=system_prompt,
    tools=[],
    history=history,
)
```

### 2. 基于 Token 数量限制

更精确的方法是基于 token 数量来限制历史：

```python
def estimate_tokens(text: str) -> int:
    """粗略估计文本的 token 数量（中文约 1.5 字符/token，英文约 4 字符/token）。"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def trim_history_by_tokens(
    history: list[Message],
    max_tokens: int = 4000
) -> list[Message]:
    """根据 token 数量限制历史。"""
    total_tokens = 0
    trimmed_history: list[Message] = []
    
    # 从最新的消息开始倒序遍历
    for message in reversed(history):
        content_str = (
            message.content
            if isinstance(message.content, str)
            else " ".join(
                part.text for part in message.content if isinstance(part, TextPart)
            )
        )
        msg_tokens = estimate_tokens(content_str)
        
        if total_tokens + msg_tokens > max_tokens:
            break
        
        total_tokens += msg_tokens
        trimmed_history.insert(0, message)
    
    return trimmed_history


# 使用示例
history.append(Message(role="user", content=user_input))
history = trim_history_by_tokens(history, max_tokens=4000)
```

### 3. 智能摘要策略

对于长对话，可以定期生成摘要来压缩历史：

```python
async def summarize_history(
    chat_provider,
    history: list[Message]
) -> str:
    """生成对话历史的摘要。"""
    # 构建摘要请求
    conversation_text = "\n".join(
        f"{msg.role}: {msg.content}" for msg in history
    )
    
    summary_prompt = f"""请简要总结以下对话的关键信息：

{conversation_text}

总结应该包含：
1. 用户的主要需求或问题
2. 已经讨论的重要信息
3. 当前对话的状态

总结："""
    
    result = await kosong.generate(
        chat_provider=chat_provider,
        system_prompt="你是一个专业的对话摘要助手。",
        tools=[],
        history=[Message(role="user", content=summary_prompt)],
    )
    
    return result.message.content if isinstance(result.message.content, str) else ""


async def manage_long_conversation(
    chat_provider,
    history: list[Message],
    max_messages: int = 30
) -> list[Message]:
    """管理长对话，必要时生成摘要。"""
    if len(history) <= max_messages:
        return history
    
    # 保留最近的消息
    recent_messages = history[-10:]
    
    # 对较早的消息生成摘要
    old_messages = history[:-10]
    summary = await summarize_history(chat_provider, old_messages)
    
    # 创建新的历史，包含摘要和最近消息
    new_history = [
        Message(role="system", content=f"对话历史摘要：{summary}")
    ]
    new_history.extend(recent_messages)
    
    return new_history
```

## 对话状态持久化

### 1. 保存到 JSON 文件

```python
import json
from pathlib import Path

from kosong.message import Message


def save_conversation(history: list[Message], filepath: str) -> None:
    """将对话历史保存到 JSON 文件。"""
    data = [msg.model_dump() for msg in history]
    Path(filepath).write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_conversation(filepath: str) -> list[Message]:
    """从 JSON 文件加载对话历史。"""
    if not Path(filepath).exists():
        return []
    
    data = json.loads(Path(filepath).read_text())
    return [Message.model_validate(msg) for msg in data]


# 使用示例
async def persistent_chat() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    conversation_file = "conversation_history.json"
    
    # 加载之前的对话历史
    history = load_conversation(conversation_file)
    
    if history:
        print(f"已加载 {len(history)} 条历史消息\n")
    
    system_prompt = "你是一个友好的助手。"

    while True:
        user_input = input("你: ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "退出"}:
            # 退出前保存对话
            save_conversation(history, conversation_file)
            print(f"对话已保存到 {conversation_file}")
            break

        history.append(Message(role="user", content=user_input))

        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt=system_prompt,
            tools=[],
            history=history,
        )

        history.append(result.message)
        print(f"助手: {result.message.content}\n")

        # 定期保存（每 5 轮对话）
        if len(history) % 10 == 0:
            save_conversation(history, conversation_file)


asyncio.run(persistent_chat())
```

### 2. 保存到数据库

对于生产环境，建议使用数据库来存储对话历史：

```python
import json
import sqlite3
from datetime import datetime

from kosong.message import Message


class ConversationDB:
    """简单的对话历史数据库管理器。"""

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_message(self, session_id: str, message: Message) -> None:
        """保存单条消息。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content = (
            message.content
            if isinstance(message.content, str)
            else json.dumps([p.model_dump() for p in message.content])
        )
        
        cursor.execute(
            "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, message.role, content),
        )
        conn.commit()
        conn.close()

    def load_session(self, session_id: str, limit: int = 100) -> list[Message]:
        """加载指定会话的历史消息。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT role, content FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        # 反转顺序（从旧到新）
        messages = []
        for role, content in reversed(rows):
            try:
                # 尝试解析为 JSON（复杂内容）
                content_data = json.loads(content)
                messages.append(Message(role=role, content=content_data))
            except json.JSONDecodeError:
                # 简单文本内容
                messages.append(Message(role=role, content=content))
        
        return messages

    def clear_session(self, session_id: str) -> None:
        """清除指定会话的历史。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()


# 使用示例
async def chat_with_db(session_id: str = "default") -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    db = ConversationDB()
    history = db.load_session(session_id)
    
    if history:
        print(f"已加载会话 '{session_id}' 的 {len(history)} 条历史消息\n")

    system_prompt = "你是一个友好的助手。"

    while True:
        user_input = input("你: ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "退出"}:
            print("再见！")
            break

        user_message = Message(role="user", content=user_input)
        history.append(user_message)
        db.save_message(session_id, user_message)

        result = await kosong.generate(
            chat_provider=kimi,
            system_prompt=system_prompt,
            tools=[],
            history=history,
        )

        history.append(result.message)
        db.save_message(session_id, result.message)
        
        print(f"助手: {result.message.content}\n")


asyncio.run(chat_with_db(session_id="user_123"))
```

## 最佳实践

### 1. 合理管理历史长度

- 根据模型的上下文窗口大小设置合理的历史长度限制
- 对于 Kimi 等长上下文模型，可以保留更多历史
- 定期清理不重要的历史消息

### 2. 处理异常情况

```python
async def safe_chat_loop() -> None:
    """带错误处理的聊天循环。"""
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    system_prompt = "你是一个友好的助手。"
    history: list[Message] = []

    while True:
        user_input = input("你: ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "退出"}:
            break

        # 临时保存用户消息
        user_message = Message(role="user", content=user_input)
        history.append(user_message)

        try:
            result = await kosong.generate(
                chat_provider=kimi,
                system_prompt=system_prompt,
                tools=[],
                history=history,
            )

            history.append(result.message)
            print(f"助手: {result.message.content}\n")

        except Exception as e:
            print(f"发生错误: {e}")
            # 移除导致错误的用户消息
            history.pop()
            print("请重试。\n")


asyncio.run(safe_chat_loop())
```

### 3. 优化性能

- 使用流式输出提供更好的用户体验（参见[流式输出指南](./streaming-output.md)）
- 考虑使用异步处理来并发处理多个用户的对话
- 对于高频访问的历史，使用缓存减少数据库查询

### 4. 保护用户隐私

- 对敏感信息进行加密存储
- 定期清理过期的对话历史
- 遵守数据保护法规（如 GDPR）

## 常见问题

### Q: 对话历史应该保留多长？

A: 这取决于你的应用场景和使用的模型：

- 对于短期任务（如单次查询），保留 5-10 轮对话即可
- 对于长期对话（如客服），可以保留 20-50 轮
- 对于长上下文模型（如 Kimi），可以保留更多历史
- 始终监控 token 使用量和响应时间

### Q: 如何处理工具调用的历史？

A: 工具调用和工具结果都应该添加到历史中：

```python
# 添加助手消息（包含工具调用）
history.append(result.message)

# 添加工具结果消息
tool_results = await result.tool_results()
tool_messages = [tool_result_to_message(tr) for tr in tool_results]
history.extend(tool_messages)
```

### Q: 如何实现多用户对话管理？

A: 为每个用户维护独立的会话 ID 和历史：

```python
# 使用字典存储多个用户的历史
user_histories: dict[str, list[Message]] = {}

def get_user_history(user_id: str) -> list[Message]:
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]

# 使用时
history = get_user_history(user_id)
```

### Q: 如何在对话中切换话题？

A: 可以通过以下方式：

1. 清空历史开始新对话
2. 使用系统消息标记话题切换
3. 生成摘要后开始新话题

```python
# 方法 1: 清空历史
history.clear()

# 方法 2: 添加系统消息
history.append(Message(
    role="system",
    content="用户现在想讨论新话题，之前的上下文不再相关。"
))

# 方法 3: 生成摘要
summary = await summarize_history(chat_provider, history)
history = [Message(role="system", content=f"之前讨论摘要：{summary}")]
```

## 下一步

- 学习[流式输出](./streaming-output.md)优化用户体验
- 学习[自定义工具](./custom-tools.md)扩展 Agent 能力
- 学习[错误处理](./error-handling.md)提高应用稳定性
- 阅读[生产部署](./production-deployment.md)准备上线

## 相关资源

- [API 参考 - generate](../api-reference/generate.md)
- [API 参考 - step](../api-reference/step.md)
- [API 参考 - Message](../api-reference/message.md)
- [核心概念](../core-concepts.md)
