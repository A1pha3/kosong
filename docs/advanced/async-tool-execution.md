# 异步工具执行

## 概述

Kosong 的工具执行系统采用异步并发设计，允许多个工具调用同时执行，从而提高整体性能。当 LLM 在一次响应中生成多个工具调用时，这些工具会立即开始并发执行，而不是按顺序等待。

本文档深入讲解：
- 工具并发执行的机制
- `ToolResultFuture` 的使用方法
- 取消和超时处理策略
- 如何实现自定义 `Toolset`

## 工具并发执行机制

### 执行流程

当 `step()` 函数接收到流式消息时，每个完整的 `ToolCall` 会立即触发工具执行：

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
    tool_calls: list[ToolCall] = []
    tool_result_futures: dict[str, ToolResultFuture] = {}

    async def on_tool_call(tool_call: ToolCall):
        tool_calls.append(tool_call)
        result = toolset.handle(tool_call)  # 立即处理工具调用

        if isinstance(result, ToolResult):
            # 同步结果：立即完成
            future = ToolResultFuture()
            future.set_result(result)
            tool_result_futures[tool_call.id] = future
        else:
            # 异步结果：保存 Future 供后续 await
            tool_result_futures[tool_call.id] = result

    result = await generate(
        chat_provider,
        system_prompt,
        toolset.tools,
        history,
        on_tool_call=on_tool_call,
    )

    return StepResult(
        result.id,
        result.message,
        result.usage,
        tool_calls,
        tool_result_futures,
    )
```

### 并发执行的优势

假设 LLM 生成了三个工具调用：

```python
# 工具调用 1: 查询天气（需要 2 秒）
# 工具调用 2: 查询新闻（需要 3 秒）
# 工具调用 3: 查询股票（需要 1 秒）
```

**串行执行**：总耗时 = 2 + 3 + 1 = 6 秒

**并发执行**：总耗时 = max(2, 3, 1) = 3 秒

Kosong 采用并发执行，显著提升性能。


## ToolResultFuture 的使用

### 什么是 ToolResultFuture

`ToolResultFuture` 是 `asyncio.Future[ToolResult]` 的类型别名，用于表示一个异步工具调用的结果：

```python
from asyncio import Future
from kosong.tooling import ToolResult

ToolResultFuture = Future[ToolResult]
```

### 获取工具结果

`StepResult` 提供了 `tool_results()` 方法来等待所有工具执行完成：

```python
import asyncio
from kosong import step, StepResult
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset

async def main():
    kimi = Kimi(api_key="your_api_key", model="kimi-k2-turbo-preview")
    toolset = SimpleToolset()
    # ... 添加工具 ...

    history = [
        Message(role="user", content="查询北京的天气和最新新闻"),
    ]

    # 执行一步，工具会立即开始并发执行
    result: StepResult = await step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )

    # 等待所有工具执行完成
    tool_results = await result.tool_results()
    
    for tool_result in tool_results:
        print(f"工具调用 ID: {tool_result.tool_call_id}")
        print(f"结果: {tool_result.result}")

asyncio.run(main())
```

### 实时监控工具结果

使用 `on_tool_result` 回调可以在工具完成时立即获得通知：

```python
from kosong.tooling import ToolResult

def handle_tool_result(result: ToolResult):
    print(f"工具 {result.tool_call_id} 完成")
    if isinstance(result.result, ToolOk):
        print(f"成功: {result.result.output}")
    else:
        print(f"失败: {result.result.message}")

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=toolset,
    history=history,
    on_tool_result=handle_tool_result,  # 实时回调
)

# 仍然可以等待所有结果
tool_results = await result.tool_results()
```

### 工具结果的顺序保证

`tool_results()` 返回的结果列表与 `tool_calls` 列表的顺序一致：

```python
result = await step(...)

# tool_calls 和 tool_results 的顺序对应
for tool_call, tool_result in zip(result.tool_calls, await result.tool_results()):
    assert tool_call.id == tool_result.tool_call_id
    print(f"{tool_call.function.name} -> {tool_result.result}")
```


## 取消和超时处理

### 取消工具执行

当 `step()` 被取消时（例如用户中断），所有正在执行的工具会自动取消：

```python
import asyncio

async def main():
    task = asyncio.create_task(
        step(
            chat_provider=kimi,
            system_prompt="你是一个助手",
            toolset=toolset,
            history=history,
        )
    )

    # 等待 1 秒后取消
    await asyncio.sleep(1)
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("步骤已取消，所有工具执行已停止")
```

### 实现超时控制

使用 `asyncio.wait_for()` 为整个步骤设置超时：

```python
import asyncio

async def main():
    try:
        result = await asyncio.wait_for(
            step(
                chat_provider=kimi,
                system_prompt="你是一个助手",
                toolset=toolset,
                history=history,
            ),
            timeout=10.0,  # 10 秒超时
        )
        tool_results = await result.tool_results()
    except asyncio.TimeoutError:
        print("步骤执行超时")
```

### 为单个工具设置超时

在自定义 `Toolset` 中，可以为每个工具调用设置独立的超时：

```python
import asyncio
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset
from kosong.tooling.error import ToolRuntimeError

class TimeoutToolset(Toolset):
    def __init__(self, base_toolset: Toolset, timeout: float = 5.0):
        self._base_toolset = base_toolset
        self._timeout = timeout

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            return result

        # 为异步结果添加超时
        async def _with_timeout():
            try:
                return await asyncio.wait_for(result, timeout=self._timeout)
            except asyncio.TimeoutError:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    result=ToolRuntimeError(
                        f"工具 {tool_call.function.name} 执行超时（{self._timeout}秒）"
                    ),
                )

        return asyncio.create_task(_with_timeout())

# 使用示例
base_toolset = SimpleToolset()
# ... 添加工具 ...

timeout_toolset = TimeoutToolset(base_toolset, timeout=3.0)

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=timeout_toolset,  # 使用带超时的 toolset
    history=history,
)
```


## 自定义 Toolset 实现

### Toolset 协议

`Toolset` 是一个 Protocol，定义了工具集的接口：

```python
from typing import Protocol
from kosong.message import ToolCall
from kosong.tooling import HandleResult, Tool

class Toolset(Protocol):
    @property
    def tools(self) -> list[Tool]:
        """返回工具集中的所有工具定义"""
        ...

    def handle(self, tool_call: ToolCall) -> HandleResult:
        """
        处理工具调用，返回 ToolResult 或 ToolResultFuture
        
        重要约束：
        - 此方法必须是非阻塞的（在流式处理期间调用）
        - 不能抛出异常（除了 asyncio.CancelledError）
        - 所有错误应返回为 ToolError
        """
        ...
```

### 示例 1：日志记录 Toolset

包装现有 toolset，添加日志记录功能：

```python
import asyncio
from datetime import datetime
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset

class LoggingToolset(Toolset):
    """为工具调用添加日志记录"""

    def __init__(self, base_toolset: Toolset):
        self._base_toolset = base_toolset

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        start_time = datetime.now()
        print(f"[{start_time}] 开始执行工具: {tool_call.function.name}")

        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            # 同步结果
            duration = (datetime.now() - start_time).total_seconds()
            print(f"[{datetime.now()}] 工具 {tool_call.function.name} 完成 ({duration:.2f}s)")
            return result

        # 异步结果：包装 Future 以记录完成时间
        async def _with_logging():
            tool_result = await result
            duration = (datetime.now() - start_time).total_seconds()
            print(f"[{datetime.now()}] 工具 {tool_call.function.name} 完成 ({duration:.2f}s)")
            return tool_result

        return asyncio.create_task(_with_logging())

# 使用示例
base_toolset = SimpleToolset()
# ... 添加工具 ...

logging_toolset = LoggingToolset(base_toolset)

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=logging_toolset,
    history=history,
)
```


### 示例 2：限流 Toolset

限制并发执行的工具数量：

```python
import asyncio
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset

class RateLimitedToolset(Toolset):
    """限制并发工具执行数量"""

    def __init__(self, base_toolset: Toolset, max_concurrent: int = 3):
        self._base_toolset = base_toolset
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            return result

        # 使用信号量限制并发
        async def _with_rate_limit():
            async with self._semaphore:
                return await result

        return asyncio.create_task(_with_rate_limit())

# 使用示例
base_toolset = SimpleToolset()
# ... 添加工具 ...

# 最多同时执行 2 个工具
rate_limited_toolset = RateLimitedToolset(base_toolset, max_concurrent=2)

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=rate_limited_toolset,
    history=history,
)
```

### 示例 3：重试 Toolset

为失败的工具调用添加自动重试：

```python
import asyncio
from kosong.tooling import HandleResult, ToolCall, ToolError, ToolResult, Toolset

class RetryToolset(Toolset):
    """为工具调用添加重试机制"""

    def __init__(self, base_toolset: Toolset, max_retries: int = 3, delay: float = 1.0):
        self._base_toolset = base_toolset
        self._max_retries = max_retries
        self._delay = delay

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        async def _with_retry():
            last_error = None
            
            for attempt in range(self._max_retries):
                # 每次重试都调用 handle 获取新的结果
                result = self._base_toolset.handle(tool_call)
                
                if isinstance(result, ToolResult):
                    tool_result = result
                else:
                    tool_result = await result

                # 检查是否成功
                if not isinstance(tool_result.result, ToolError):
                    if attempt > 0:
                        print(f"工具 {tool_call.function.name} 在第 {attempt + 1} 次尝试成功")
                    return tool_result

                last_error = tool_result
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self._max_retries - 1:
                    print(f"工具 {tool_call.function.name} 失败，{self._delay}秒后重试...")
                    await asyncio.sleep(self._delay)

            # 所有重试都失败
            print(f"工具 {tool_call.function.name} 在 {self._max_retries} 次尝试后仍然失败")
            return last_error

        return asyncio.create_task(_with_retry())

# 使用示例
base_toolset = SimpleToolset()
# ... 添加工具 ...

retry_toolset = RetryToolset(base_toolset, max_retries=3, delay=1.0)

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=retry_toolset,
    history=history,
)
```


### 示例 4：缓存 Toolset

缓存工具调用结果，避免重复执行：

```python
import asyncio
import hashlib
import json
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset

class CachedToolset(Toolset):
    """缓存工具调用结果"""

    def __init__(self, base_toolset: Toolset):
        self._base_toolset = base_toolset
        self._cache: dict[str, ToolResult] = {}

    @property
    def tools(self):
        return self._base_toolset.tools

    def _get_cache_key(self, tool_call: ToolCall) -> str:
        """生成缓存键"""
        data = f"{tool_call.function.name}:{tool_call.function.arguments}"
        return hashlib.md5(data.encode()).hexdigest()

    def handle(self, tool_call: ToolCall) -> HandleResult:
        cache_key = self._get_cache_key(tool_call)

        # 检查缓存
        if cache_key in self._cache:
            print(f"使用缓存结果: {tool_call.function.name}")
            cached_result = self._cache[cache_key]
            # 返回新的 ToolResult，使用当前的 tool_call_id
            return ToolResult(
                tool_call_id=tool_call.id,
                result=cached_result.result,
            )

        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            # 同步结果：直接缓存
            self._cache[cache_key] = result
            return result

        # 异步结果：等待完成后缓存
        async def _with_cache():
            tool_result = await result
            self._cache[cache_key] = tool_result
            return tool_result

        return asyncio.create_task(_with_cache())

# 使用示例
base_toolset = SimpleToolset()
# ... 添加工具 ...

cached_toolset = CachedToolset(base_toolset)

# 第一次调用会执行工具
result1 = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=cached_toolset,
    history=[Message(role="user", content="查询北京天气")],
)

# 第二次相同的调用会使用缓存
result2 = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=cached_toolset,
    history=[Message(role="user", content="查询北京天气")],
)
```

### 组合多个 Toolset

可以将多个 Toolset 装饰器组合使用：

```python
base_toolset = SimpleToolset()
# ... 添加工具 ...

# 组合：日志 + 限流 + 重试 + 缓存
toolset = CachedToolset(
    RetryToolset(
        RateLimitedToolset(
            LoggingToolset(base_toolset),
            max_concurrent=3
        ),
        max_retries=2
    )
)

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=toolset,
    history=history,
)
```


## 最佳实践

### 1. handle() 方法必须非阻塞

`handle()` 方法在流式处理期间被调用，必须立即返回：

```python
# ❌ 错误：阻塞操作
def handle(self, tool_call: ToolCall) -> HandleResult:
    result = requests.get("https://api.example.com")  # 阻塞！
    return ToolResult(tool_call.id, ToolOk(output=result.text))

# ✅ 正确：异步操作
def handle(self, tool_call: ToolCall) -> HandleResult:
    async def _fetch():
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.example.com") as response:
                text = await response.text()
                return ToolResult(tool_call.id, ToolOk(output=text))
    
    return asyncio.create_task(_fetch())
```

### 2. 错误应返回为 ToolError

不要在 `handle()` 中抛出异常（除了 `asyncio.CancelledError`）：

```python
# ❌ 错误：抛出异常
def handle(self, tool_call: ToolCall) -> HandleResult:
    if tool_call.function.name not in self._tools:
        raise ValueError(f"工具不存在: {tool_call.function.name}")

# ✅ 正确：返回 ToolError
def handle(self, tool_call: ToolCall) -> HandleResult:
    if tool_call.function.name not in self._tools:
        return ToolResult(
            tool_call.id,
            ToolNotFoundError(tool_call.function.name)
        )
```

### 3. 正确处理取消

工具执行应该能够响应取消请求：

```python
async def _long_running_task():
    try:
        for i in range(100):
            await asyncio.sleep(0.1)
            # 定期检查是否被取消
            if asyncio.current_task().cancelled():
                break
            # 执行工作...
    except asyncio.CancelledError:
        # 清理资源
        print("任务被取消，正在清理...")
        raise  # 重新抛出 CancelledError
```

### 4. 避免共享可变状态

如果 Toolset 有状态，确保线程安全：

```python
import asyncio
from collections import defaultdict

class StatefulToolset(Toolset):
    def __init__(self, base_toolset: Toolset):
        self._base_toolset = base_toolset
        self._call_counts: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()  # 使用锁保护共享状态

    def handle(self, tool_call: ToolCall) -> HandleResult:
        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            return result

        async def _with_counting():
            tool_result = await result
            
            # 使用锁保护共享状态
            async with self._lock:
                self._call_counts[tool_call.function.name] += 1
            
            return tool_result

        return asyncio.create_task(_with_counting())
```

### 5. 合理设置超时

为长时间运行的工具设置合理的超时：

```python
# 根据工具类型设置不同的超时
class SmartTimeoutToolset(Toolset):
    def __init__(self, base_toolset: Toolset):
        self._base_toolset = base_toolset
        self._timeouts = {
            "search_web": 10.0,      # 网络搜索：10秒
            "query_database": 5.0,   # 数据库查询：5秒
            "generate_image": 30.0,  # 图像生成：30秒
        }
        self._default_timeout = 15.0

    def handle(self, tool_call: ToolCall) -> HandleResult:
        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            return result

        timeout = self._timeouts.get(
            tool_call.function.name,
            self._default_timeout
        )

        async def _with_timeout():
            try:
                return await asyncio.wait_for(result, timeout=timeout)
            except asyncio.TimeoutError:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    result=ToolRuntimeError(
                        f"工具 {tool_call.function.name} 执行超时"
                    ),
                )

        return asyncio.create_task(_with_timeout())
```


## 性能优化建议

### 1. 使用连接池

对于需要网络请求的工具，使用连接池可以提高性能：

```python
import aiohttp
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from pydantic import BaseModel

class SearchParams(BaseModel):
    query: str

class SearchTool(CallableTool2[SearchParams]):
    name: str = "search"
    description: str = "搜索网络"
    params: type[SearchParams] = SearchParams

    def __init__(self):
        super().__init__()
        # 创建共享的 session（连接池）
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def __call__(self, params: SearchParams) -> ToolReturnType:
        session = await self._get_session()
        async with session.get(
            "https://api.example.com/search",
            params={"q": params.query}
        ) as response:
            result = await response.text()
            return ToolOk(output=result)

    async def close(self):
        """清理资源"""
        if self._session and not self._session.closed:
            await self._session.close()
```

### 2. 批量处理

如果多个工具调用可以批量处理，考虑实现批量优化：

```python
import asyncio
from collections import defaultdict
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset

class BatchingToolset(Toolset):
    """将相同类型的工具调用批量处理"""

    def __init__(self, base_toolset: Toolset, batch_delay: float = 0.1):
        self._base_toolset = base_toolset
        self._batch_delay = batch_delay
        self._pending_calls: dict[str, list[tuple[ToolCall, asyncio.Future]]] = defaultdict(list)
        self._batch_tasks: dict[str, asyncio.Task] = {}

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        tool_name = tool_call.function.name
        future = asyncio.Future()
        
        self._pending_calls[tool_name].append((tool_call, future))

        # 如果还没有批处理任务，创建一个
        if tool_name not in self._batch_tasks:
            self._batch_tasks[tool_name] = asyncio.create_task(
                self._process_batch(tool_name)
            )

        return future

    async def _process_batch(self, tool_name: str):
        """等待一小段时间收集批次，然后处理"""
        await asyncio.sleep(self._batch_delay)
        
        calls = self._pending_calls.pop(tool_name, [])
        del self._batch_tasks[tool_name]

        if not calls:
            return

        print(f"批量处理 {len(calls)} 个 {tool_name} 调用")

        # 并发执行所有调用
        tasks = []
        for tool_call, future in calls:
            result = self._base_toolset.handle(tool_call)
            if isinstance(result, ToolResult):
                future.set_result(result)
            else:
                tasks.append((result, future))

        # 等待所有异步结果
        for result_future, output_future in tasks:
            try:
                result = await result_future
                output_future.set_result(result)
            except Exception as e:
                output_future.set_exception(e)
```

### 3. 监控和指标

添加性能监控以识别瓶颈：

```python
import time
from collections import defaultdict
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset

class MetricsToolset(Toolset):
    """收集工具执行指标"""

    def __init__(self, base_toolset: Toolset):
        self._base_toolset = base_toolset
        self._metrics = {
            "call_count": defaultdict(int),
            "total_duration": defaultdict(float),
            "error_count": defaultdict(int),
        }

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        start_time = time.time()
        tool_name = tool_call.function.name
        
        self._metrics["call_count"][tool_name] += 1
        
        result = self._base_toolset.handle(tool_call)

        if isinstance(result, ToolResult):
            duration = time.time() - start_time
            self._metrics["total_duration"][tool_name] += duration
            if isinstance(result.result, ToolError):
                self._metrics["error_count"][tool_name] += 1
            return result

        async def _with_metrics():
            tool_result = await result
            duration = time.time() - start_time
            self._metrics["total_duration"][tool_name] += duration
            if isinstance(tool_result.result, ToolError):
                self._metrics["error_count"][tool_name] += 1
            return tool_result

        return asyncio.create_task(_with_metrics())

    def get_metrics(self) -> dict:
        """获取性能指标"""
        metrics = {}
        for tool_name in self._metrics["call_count"]:
            count = self._metrics["call_count"][tool_name]
            total_duration = self._metrics["total_duration"][tool_name]
            error_count = self._metrics["error_count"][tool_name]
            
            metrics[tool_name] = {
                "call_count": count,
                "avg_duration": total_duration / count if count > 0 else 0,
                "error_rate": error_count / count if count > 0 else 0,
            }
        return metrics
```


## 常见问题

### Q: 为什么 handle() 必须非阻塞？

A: `handle()` 在流式处理消息期间被调用。如果 `handle()` 阻塞，会导致整个消息流处理停滞，影响用户体验。通过返回 `Future`，工具可以在后台异步执行，而消息流继续处理。

### Q: 如何确保工具按特定顺序执行？

A: Kosong 默认并发执行工具以提高性能。如果需要顺序执行，可以实现自定义 Toolset：

```python
import asyncio
from kosong.tooling import HandleResult, ToolCall, ToolResult, Toolset

class SequentialToolset(Toolset):
    """按顺序执行工具调用"""

    def __init__(self, base_toolset: Toolset):
        self._base_toolset = base_toolset
        self._queue: asyncio.Queue[tuple[ToolCall, asyncio.Future]] = asyncio.Queue()
        self._worker_task = asyncio.create_task(self._worker())

    @property
    def tools(self):
        return self._base_toolset.tools

    def handle(self, tool_call: ToolCall) -> HandleResult:
        future = asyncio.Future()
        self._queue.put_nowait((tool_call, future))
        return future

    async def _worker(self):
        """工作线程：按顺序处理队列中的工具调用"""
        while True:
            tool_call, future = await self._queue.get()
            
            try:
                result = self._base_toolset.handle(tool_call)
                if isinstance(result, ToolResult):
                    future.set_result(result)
                else:
                    tool_result = await result
                    future.set_result(tool_result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self._queue.task_done()
```

### Q: 如何处理工具执行中的异常？

A: 工具执行中的异常应该被捕获并转换为 `ToolError`：

```python
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType
from pydantic import BaseModel

class MyToolParams(BaseModel):
    value: int

class MyTool(CallableTool2[MyToolParams]):
    name: str = "my_tool"
    description: str = "示例工具"
    params: type[MyToolParams] = MyToolParams

    async def __call__(self, params: MyToolParams) -> ToolReturnType:
        try:
            # 可能抛出异常的操作
            result = await some_risky_operation(params.value)
            return ToolOk(output=str(result))
        except ValueError as e:
            # 转换为 ToolError
            return ToolError(
                message=f"参数错误: {e}",
                brief="参数错误"
            )
        except Exception as e:
            # 捕获所有其他异常
            return ToolError(
                message=f"工具执行失败: {e}",
                brief="执行失败"
            )
```

### Q: 可以在 handle() 中访问其他工具的结果吗？

A: 不建议这样做，因为工具是并发执行的，无法保证执行顺序。如果工具之间有依赖关系，应该：

1. 在 Agent 循环中处理依赖（让 LLM 决定调用顺序）
2. 将相关功能合并到一个工具中
3. 使用 SequentialToolset 强制顺序执行

### Q: 如何调试工具执行问题？

A: 使用 LoggingToolset 或 `on_tool_result` 回调：

```python
from kosong.tooling import ToolResult, ToolError

def debug_tool_result(result: ToolResult):
    print(f"\n=== 工具结果 ===")
    print(f"ID: {result.tool_call_id}")
    
    if isinstance(result.result, ToolError):
        print(f"状态: 失败")
        print(f"错误: {result.result.message}")
    else:
        print(f"状态: 成功")
        print(f"输出: {result.result.output}")
    print(f"================\n")

result = await step(
    chat_provider=kimi,
    system_prompt="你是一个助手",
    toolset=toolset,
    history=history,
    on_tool_result=debug_tool_result,  # 调试回调
)
```

## 相关文档

- [工具系统 API 参考](../api-reference/tooling.md) - 详细的 API 文档
- [自定义工具](../guides/custom-tools.md) - 如何创建自定义工具
- [架构设计](../architecture.md) - 了解工具调用的整体架构
- [错误处理](../guides/error-handling.md) - 工具错误处理最佳实践

## 总结

Kosong 的异步工具执行系统提供了：

- **并发执行**：多个工具同时执行，提高性能
- **灵活扩展**：通过 Toolset Protocol 实现自定义逻辑
- **可靠性**：内置取消和错误处理机制
- **可组合性**：多个 Toolset 可以组合使用

通过理解 `ToolResultFuture` 和 `Toolset` 协议，你可以构建高性能、可靠的 AI Agent 应用。
