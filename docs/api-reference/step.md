---
title: kosong.step
description: 执行一个完整的 Agent 步骤（包含工具调用处理）
version: 0.23.0
last_updated: 2025-01-15
---

# kosong.step

> 执行一个完整的 Agent 步骤，自动处理工具调用和结果收集。

`step()` 函数是 Kosong 构建 AI Agent 的核心函数。它在 `generate()` 的基础上增加了自动工具执行功能，会生成 LLM 响应并自动调用工具集（Toolset）来处理工具调用，返回包含工具结果的 `StepResult` 对象。

## 函数签名

```python
async def step(
    chat_provider: ChatProvider,
    system_prompt: str,
    toolset: Toolset,
    history: Sequence[Message],
    *,
    on_message_part: Callback[[StreamedMessagePart], None] | None = None,
    on_tool_result: Callable[[ToolResult], None] | None = None,
) -> StepResult:
    """
    Run one agent "step". In one step, the function generates LLM response based on the given
    context for exactly one time. All new message parts will be streamed to `on_message_part` in
    real-time if provided. Tool calls will be handled by `toolset`. The generated message will be
    returned in a `StepResult`. Depending on the toolset implementation, the tool calls may be
    handled asynchronously and the results need to be fetched with `await result.tool_results()`.
    """
    ...
```

## 参数说明

### 必需参数

- **chat_provider** (`ChatProvider`): 用于生成响应的聊天提供者实例，例如 `Kimi`、`Anthropic` 等
- **system_prompt** (`str`): 系统提示词，用于设定 AI Agent 的角色和行为规范
- **toolset** (`Toolset`): 工具集对象，负责处理和执行工具调用。常用的实现有 `SimpleToolset`
- **history** (`Sequence[Message]`): 对话历史消息列表，按时间顺序排列

### 可选参数

- **on_message_part** (`Callback[[StreamedMessagePart], None] | None`, 默认值: `None`): 
  流式消息片段回调函数。每当接收到一个消息片段时会被调用，可用于实时显示响应内容。回调函数可以是同步或异步函数。

- **on_tool_result** (`Callable[[ToolResult], None] | None`, 默认值: `None`): 
  工具结果回调函数。每当一个工具执行完成时会被调用。注意这是同步或异步的 Callable，不是 Callback 类型。

## 返回值

**类型：** `StepResult`

返回一个 `StepResult` 对象，包含以下字段和方法：

### StepResult 字段

- **id** (`str | None`): 生成消息的唯一标识符（如果 ChatProvider 提供）
- **message** (`Message`): 生成的完整消息对象，包含 LLM 的响应内容和工具调用
- **usage** (`TokenUsage | None`): Token 使用统计信息（如果 ChatProvider 提供）
- **tool_calls** (`list[ToolCall]`): 本步骤中生成的所有工具调用列表

### StepResult 方法

- **async tool_results() -> list[ToolResult]**: 
  异步方法，等待并返回所有工具调用的执行结果。根据 Toolset 的实现，工具可能是异步执行的，此方法会等待所有工具执行完成。

## 异常

- **APIConnectionError**: API 连接失败时抛出
- **APITimeoutError**: API 请求超时时抛出
- **APIStatusError**: API 返回 4xx 或 5xx 状态码时抛出
- **APIEmptyResponseError**: API 返回空响应时抛出
- **ChatProviderError**: 其他聊天提供者相关错误
- **asyncio.CancelledError**: 步骤被取消时抛出

## 使用示例

### 示例 1：基础 Agent 步骤

```python
# 基础 Agent 步骤示例

import asyncio
from pydantic import BaseModel
from kosong import step
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset

# 定义工具参数
class AddToolParams(BaseModel):
    a: int
    b: int

# 定义工具
class AddTool(CallableTool2[AddToolParams]):
    name: str = "add"
    description: str = "将两个整数相加"
    params: type[AddToolParams] = AddToolParams

    async def __call__(self, params: AddToolParams) -> ToolReturnType:
        result = params.a + params.b
        return ToolOk(output=str(result))

async def main() -> None:
    # 创建 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    # 创建工具集
    toolset = SimpleToolset()
    toolset += AddTool()
    
    # 准备对话历史
    history = [
        Message(role="user", content="请用 add 工具计算 2 + 3"),
    ]
    
    # 执行一个步骤
    result = await step(
        chat_provider=kimi,
        system_prompt="你是一个数学助手。",
        toolset=toolset,
        history=history,
    )
    
    print(f"助手响应: {result.message.content}")
    print(f"工具调用数量: {len(result.tool_calls)}")
    
    # 获取工具执行结果
    tool_results = await result.tool_results()
    for tr in tool_results:
        print(f"工具 {tr.tool_call.name} 返回: {tr.output}")

asyncio.run(main())
```

**输出：**
```
助手响应: [工具调用请求]
工具调用数量: 1
工具 add 返回: 5
```


### 示例 2：流式输出和工具结果回调

```python
# 流式输出和工具结果回调示例

import asyncio
from pydantic import BaseModel
from kosong import step
from kosong.chat_provider.kimi import Kimi
from kosong.chat_provider import StreamedMessagePart
from kosong.message import Message, TextPart
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType, ToolResult
from kosong.tooling.simple import SimpleToolset

class SearchToolParams(BaseModel):
    query: str

class SearchTool(CallableTool2[SearchToolParams]):
    name: str = "search"
    description: str = "搜索信息"
    params: type[SearchToolParams] = SearchToolParams

    async def __call__(self, params: SearchToolParams) -> ToolReturnType:
        # 模拟搜索
        await asyncio.sleep(1)
        return ToolOk(output=f"关于 '{params.query}' 的搜索结果...")

async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    toolset += SearchTool()
    
    history = [
        Message(role="user", content="搜索一下 Python 的最新特性"),
    ]
    
    # 定义回调函数
    async def on_part(part: StreamedMessagePart) -> None:
        if isinstance(part, TextPart):
            print(part.text, end="", flush=True)
    
    def on_result(result: ToolResult) -> None:
        print(f"\n[工具执行完成] {result.tool_call.name}: {result.output}")
    
    # 执行步骤
    result = await step(
        chat_provider=kimi,
        system_prompt="你是一个搜索助手。",
        toolset=toolset,
        history=history,
        on_message_part=on_part,
        on_tool_result=on_result,
    )
    
    print("\n\n步骤完成！")

asyncio.run(main())
```

### 示例 3：多工具 Agent

```python
# 多工具 Agent 示例

import asyncio
from pydantic import BaseModel
from kosong import step
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset

# 定义多个工具
class WeatherParams(BaseModel):
    city: str

class WeatherTool(CallableTool2[WeatherParams]):
    name: str = "get_weather"
    description: str = "获取指定城市的天气信息"
    params: type[WeatherParams] = WeatherParams

    async def __call__(self, params: WeatherParams) -> ToolReturnType:
        return ToolOk(output=f"{params.city}：晴天，25°C")

class TimeParams(BaseModel):
    timezone: str

class TimeTool(CallableTool2[TimeParams]):
    name: str = "get_time"
    description: str = "获取指定时区的当前时间"
    params: type[TimeParams] = TimeParams

    async def __call__(self, params: TimeParams) -> ToolReturnType:
        return ToolOk(output=f"{params.timezone} 时区：14:30")

async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    # 创建包含多个工具的工具集
    toolset = SimpleToolset()
    toolset += WeatherTool()
    toolset += TimeTool()
    
    history = [
        Message(role="user", content="北京的天气和时间是多少？"),
    ]
    
    result = await step(
        chat_provider=kimi,
        system_prompt="你是一个信息助手，可以查询天气和时间。",
        toolset=toolset,
        history=history,
    )
    
    # 等待所有工具执行完成
    tool_results = await result.tool_results()
    
    print(f"调用了 {len(tool_results)} 个工具：")
    for tr in tool_results:
        print(f"  - {tr.tool_call.name}: {tr.output}")

asyncio.run(main())
```

**输出：**
```
调用了 2 个工具：
  - get_weather: 北京：晴天，25°C
  - get_time: Asia/Shanghai 时区：14:30
```

### 示例 4：Agent 循环（多步骤）

```python
# Agent 循环示例

import asyncio
from pydantic import BaseModel
from kosong import step
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset

class CalculatorParams(BaseModel):
    expression: str

class CalculatorTool(CallableTool2[CalculatorParams]):
    name: str = "calculate"
    description: str = "计算数学表达式"
    params: type[CalculatorParams] = CalculatorParams

    async def __call__(self, params: CalculatorParams) -> ToolReturnType:
        try:
            result = eval(params.expression)
            return ToolOk(output=str(result))
        except Exception as e:
            return ToolOk(output=f"计算错误: {e}")

async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    toolset += CalculatorTool()
    
    # 初始化对话历史
    history: list[Message] = [
        Message(role="user", content="计算 (10 + 5) * 3，然后告诉我结果是否大于 40"),
    ]
    
    max_steps = 5
    for i in range(max_steps):
        print(f"\n--- 步骤 {i + 1} ---")
        
        # 执行一个步骤
        result = await step(
            chat_provider=kimi,
            system_prompt="你是一个数学助手。",
            toolset=toolset,
            history=history,
        )
        
        # 将助手消息添加到历史
        history.append(result.message)
        
        # 如果有工具调用，获取结果并添加到历史
        if result.tool_calls:
            print(f"调用了 {len(result.tool_calls)} 个工具")
            tool_results = await result.tool_results()
            
            # 将工具结果添加到历史
            for tr in tool_results:
                history.append(
                    Message(
                        role="tool",
                        tool_call_id=tr.tool_call.id,
                        content=tr.output,
                    )
                )
                print(f"  工具 {tr.tool_call.name} 返回: {tr.output}")
        else:
            # 没有工具调用，说明 Agent 已完成任务
            print(f"助手最终回复: {result.message.content}")
            break
    else:
        print("\n达到最大步骤数限制")

asyncio.run(main())
```

**输出：**
```
--- 步骤 1 ---
调用了 1 个工具
  工具 calculate 返回: 45

--- 步骤 2 ---
助手最终回复: 计算结果是 45，它大于 40。
```


## StepResult 详细说明

`StepResult` 是 `step()` 函数的返回类型，它封装了一个 Agent 步骤的所有信息。

### 数据类定义

```python
@dataclass(frozen=True, slots=True)
class StepResult:
    id: str | None
    """生成消息的 ID"""

    message: Message
    """本步骤生成的消息"""

    usage: TokenUsage | None
    """Token 使用统计"""

    tool_calls: list[ToolCall]
    """本步骤生成的所有工具调用"""

    _tool_result_futures: dict[str, ToolResultFuture]
    """@private 工具结果的 Future 对象"""

    async def tool_results(self) -> list[ToolResult]:
        """等待并返回所有工具调用的执行结果"""
        ...
```

### 使用 StepResult

```python
# 获取基本信息
result = await step(...)

print(f"消息 ID: {result.id}")
print(f"消息内容: {result.message.content}")
print(f"Token 使用: {result.usage}")
print(f"工具调用数: {len(result.tool_calls)}")

# 获取工具结果
if result.tool_calls:
    tool_results = await result.tool_results()
    for tr in tool_results:
        if tr.is_ok:
            print(f"工具 {tr.tool_call.name} 成功: {tr.output}")
        else:
            print(f"工具 {tr.tool_call.name} 失败: {tr.error}")
```

### 工具结果的异步特性

根据 `Toolset` 的实现，工具可能是异步执行的：

- **SimpleToolset**: 工具调用会立即开始执行，但结果需要通过 `await result.tool_results()` 获取
- 多个工具调用可能并发执行，提高效率
- `tool_results()` 方法会等待所有工具执行完成后返回

```python
# 工具可能并发执行
result = await step(...)  # 工具已开始执行

# 做一些其他工作...
await asyncio.sleep(1)

# 等待工具完成
tool_results = await result.tool_results()  # 可能立即返回（如果工具已完成）
```

## 注意事项

### 消息历史管理

`step()` 函数**不会修改**传入的 `history` 参数。如果需要构建多步骤 Agent 循环，需要手动管理历史：

```python
history: list[Message] = [initial_message]

# 步骤 1
result1 = await step(..., history=history)
history.append(result1.message)

# 如果有工具调用，添加工具结果
if result1.tool_calls:
    tool_results = await result1.tool_results()
    for tr in tool_results:
        history.append(Message(role="tool", tool_call_id=tr.tool_call.id, content=tr.output))

# 步骤 2
result2 = await step(..., history=history)
history.append(result2.message)
```

### 工具结果必须等待

如果 `StepResult` 包含工具调用，**必须**调用 `await result.tool_results()` 来获取结果，否则：

- 工具执行任务可能会泄漏
- 资源可能无法正确清理
- 可能导致程序挂起

```python
# ❌ 错误：忽略工具结果
result = await step(...)
# 直接丢弃 result，工具任务可能泄漏

# ✅ 正确：总是等待工具结果
result = await step(...)
if result.tool_calls:
    await result.tool_results()
```

### 错误处理

工具执行中的错误会被封装在 `ToolResult` 中，不会抛出异常：

```python
result = await step(...)
tool_results = await result.tool_results()

for tr in tool_results:
    if tr.is_ok:
        print(f"成功: {tr.output}")
    else:
        print(f"失败: {tr.error}")
        # 工具失败不会中断流程，可以继续处理
```

但 ChatProvider 相关的错误会直接抛出，需要捕获：

```python
try:
    result = await step(...)
except APIConnectionError as e:
    print(f"连接失败: {e}")
except asyncio.CancelledError:
    print("步骤被取消")
    raise  # 重新抛出取消异常
```

### 取消操作

如果 `step()` 被取消（通过 `asyncio.CancelledError`），所有正在执行的工具任务也会被自动取消：

```python
async def run_step():
    try:
        result = await step(...)
        return result
    except asyncio.CancelledError:
        print("步骤被取消，工具任务已清理")
        raise

# 可以安全地取消
task = asyncio.create_task(run_step())
await asyncio.sleep(1)
task.cancel()
```

### 性能优化

- 使用 `on_message_part` 实现流式输出，提升用户体验
- 使用 `on_tool_result` 实时处理工具结果，无需等待所有工具完成
- 对于不需要工具结果的场景，仍然需要调用 `await result.tool_results()` 以避免资源泄漏

## 相关 API

- [generate](./generate.md) - 底层的消息生成函数
- [Message](./message.md) - 消息对象的详细说明
- [Tooling](./tooling.md) - 工具和工具集的详细说明
- [ChatProvider](./chat-provider.md) - ChatProvider 协议和实现

## 与 generate() 的对比

| 特性 | generate() | step() |
|------|-----------|--------|
| **工具调用** | 只生成工具调用请求 | 自动执行工具并返回结果 |
| **返回类型** | GenerateResult | StepResult |
| **工具参数** | `tools: Sequence[Tool]` | `toolset: Toolset` |
| **工具执行** | 需要手动处理 | 自动处理（通过 Toolset） |
| **异步工具** | 不支持 | 支持（通过 ToolResultFuture） |
| **使用场景** | 需要完全控制工具执行流程 | 构建自动化 Agent |
| **复杂度** | 较低，更灵活 | 较高，更便捷 |

### 何时使用 generate()

- 需要自定义工具执行逻辑
- 需要在工具执行前进行额外处理
- 不需要工具功能，只需要生成响应

### 何时使用 step()

- 构建标准的 Agent 应用
- 需要自动化的工具执行流程
- 需要并发执行多个工具
- 大多数情况下的推荐选择

---

_文档版本: v0.23.0 | 最后更新: 2025-01-15_
