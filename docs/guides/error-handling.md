---
title: 错误处理指南
description: 学习如何在 Kosong 中处理 API 错误、工具执行错误，以及实现重试和优雅降级策略
version: 0.23.0
last_updated: 2025-01-15
---

# 错误处理指南

在构建 AI Agent 应用时，正确的错误处理至关重要。Kosong 提供了完善的错误处理机制，帮助你构建健壮、可靠的应用程序。本指南将介绍 Kosong 中的异常类型、错误处理最佳实践、重试策略和优雅降级方案。

## 场景说明

错误处理适用于以下场景：

- **API 调用失败**：网络问题、超时、服务器错误
- **工具执行错误**：参数验证失败、运行时异常
- **资源限制**：配额用尽、速率限制
- **数据问题**：空响应、格式错误
- **系统故障**：服务不可用、依赖失败

## 常见异常类型

Kosong 定义了一系列异常类型，帮助你精确识别和处理不同的错误情况。

### API 相关异常

所有 API 相关异常都继承自 `ChatProviderError` 基类。

#### 1. ChatProviderError

所有聊天提供商错误的基类。

```python
from kosong.chat_provider import ChatProviderError

try:
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
except ChatProviderError as e:
    # 捕获所有聊天提供商相关的错误
    print(f"聊天提供商错误: {e}")
```

#### 2. APIConnectionError

当 API 连接失败时抛出（如网络不可达、DNS 解析失败）。

```python
from kosong.chat_provider import APIConnectionError

try:
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
except APIConnectionError as e:
    print(f"API 连接失败: {e}")
    # 可能的原因：
    # - 网络断开
    # - DNS 解析失败
    # - 防火墙阻止
    # - 代理配置错误
```

#### 3. APITimeoutError

当 API 请求超时时抛出。

```python
from kosong.chat_provider import APITimeoutError

try:
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
except APITimeoutError as e:
    print(f"API 请求超时: {e}")
    # 可能的原因：
    # - 服务器响应慢
    # - 网络延迟高
    # - 请求过于复杂
```

#### 4. APIStatusError

当 API 返回 4xx 或 5xx 状态码时抛出。包含 `status_code` 属性。

```python
from kosong.chat_provider import APIStatusError

try:
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
except APIStatusError as e:
    print(f"API 状态错误: {e.status_code} - {e}")
    
    # 根据状态码采取不同的处理策略
    if e.status_code == 401:
        print("认证失败，请检查 API 密钥")
    elif e.status_code == 429:
        print("请求过于频繁，触发速率限制")
    elif e.status_code >= 500:
        print("服务器错误，可以尝试重试")
```

**常见状态码**：

- `400 Bad Request`：请求参数错误
- `401 Unauthorized`：API 密钥无效或过期
- `403 Forbidden`：没有访问权限
- `404 Not Found`：端点不存在
- `429 Too Many Requests`：超过速率限制
- `500 Internal Server Error`：服务器内部错误
- `502 Bad Gateway`：网关错误
- `503 Service Unavailable`：服务暂时不可用

#### 5. APIEmptyResponseError

当 API 返回空响应时抛出（没有内容也没有工具调用）。

```python
from kosong.chat_provider import APIEmptyResponseError

try:
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
except APIEmptyResponseError as e:
    print(f"API 返回空响应: {e}")
    # 可能的原因：
    # - 模型输出被过滤
    # - 请求被截断
    # - 服务异常
```

### 工具相关异常

工具执行过程中可能遇到的错误。注意：这些不是 Python 异常，而是工具返回的 `ToolError` 对象。

#### 1. ToolNotFoundError

工具未找到。

```python
from kosong.tooling.error import ToolNotFoundError

# 这是一个 ToolError，不是异常
# 当 AI 调用不存在的工具时，会自动返回此错误
```

#### 2. ToolParseError

工具参数不是有效的 JSON。

```python
from kosong.tooling.error import ToolParseError

# 当 AI 提供的参数无法解析为 JSON 时返回
```

#### 3. ToolValidateError

工具参数验证失败（不符合 JSON Schema 或 Pydantic 模型）。

```python
from kosong.tooling.error import ToolValidateError

# 当参数不符合工具定义的 schema 时返回
```

#### 4. ToolRuntimeError

工具运行时错误。

```python
from kosong.tooling.error import ToolRuntimeError

# 工具执行过程中发生的错误
```

## API 错误处理示例

### 基础错误处理

捕获所有可能的 API 错误：

```python
import asyncio

import kosong
from kosong.chat_provider import (
    APIConnectionError,
    APIEmptyResponseError,
    APIStatusError,
    APITimeoutError,
    ChatProviderError,
)
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset


async def safe_step(
    chat_provider,
    system_prompt: str,
    toolset,
    history,
) -> kosong.StepResult | None:
    """安全地执行一个 step，处理所有可能的错误。"""
    try:
        result = await kosong.step(
            chat_provider=chat_provider,
            system_prompt=system_prompt,
            toolset=toolset,
            history=history,
        )
        return result
    
    except APIConnectionError as e:
        print(f"❌ 连接失败: {e}")
        print("请检查网络连接和 API 端点配置")
        return None
    
    except APITimeoutError as e:
        print(f"⏱️ 请求超时: {e}")
        print("可以尝试重试或简化请求")
        return None
    
    except APIStatusError as e:
        print(f"🚫 API 错误 [{e.status_code}]: {e}")
        
        if e.status_code == 401:
            print("请检查 API 密钥是否正确")
        elif e.status_code == 429:
            print("触发速率限制，请稍后重试")
        elif e.status_code >= 500:
            print("服务器错误，可以稍后重试")
        
        return None
    
    except APIEmptyResponseError as e:
        print(f"📭 空响应: {e}")
        print("模型没有返回任何内容")
        return None
    
    except ChatProviderError as e:
        print(f"❓ 未知错误: {e}")
        return None
    
    except asyncio.CancelledError:
        print("⚠️ 操作被取消")
        raise  # 重新抛出 CancelledError
    
    except Exception as e:
        print(f"💥 意外错误: {e}")
        return None


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    history = [Message(role="user", content="你好")]
    
    result = await safe_step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
    
    if result:
        print(f"✅ 成功: {result.message.content}")
    else:
        print("处理失败")


asyncio.run(main())
```

### 分层错误处理

根据错误类型采取不同的处理策略：

```python
from typing import Literal

ErrorSeverity = Literal["fatal", "retryable", "ignorable"]


def classify_error(error: Exception) -> ErrorSeverity:
    """分类错误的严重程度。"""
    if isinstance(error, APIConnectionError):
        return "retryable"  # 网络问题，可以重试
    
    elif isinstance(error, APITimeoutError):
        return "retryable"  # 超时，可以重试
    
    elif isinstance(error, APIStatusError):
        if error.status_code == 401:
            return "fatal"  # 认证失败，无法恢复
        elif error.status_code == 429:
            return "retryable"  # 速率限制，可以重试
        elif error.status_code >= 500:
            return "retryable"  # 服务器错误，可以重试
        else:
            return "fatal"  # 其他客户端错误
    
    elif isinstance(error, APIEmptyResponseError):
        return "ignorable"  # 空响应，可以忽略或重试
    
    else:
        return "fatal"  # 未知错误


async def robust_step(
    chat_provider,
    system_prompt: str,
    toolset,
    history,
) -> kosong.StepResult | None:
    """根据错误严重程度采取不同的处理策略。"""
    try:
        return await kosong.step(
            chat_provider=chat_provider,
            system_prompt=system_prompt,
            toolset=toolset,
            history=history,
        )
    
    except ChatProviderError as e:
        severity = classify_error(e)
        
        if severity == "fatal":
            print(f"致命错误，无法继续: {e}")
            raise
        
        elif severity == "retryable":
            print(f"可重试错误: {e}")
            return None
        
        else:  # ignorable
            print(f"可忽略错误: {e}")
            return None
```


## 工具执行错误处理

工具错误不是 Python 异常，而是通过 `ToolError` 对象返回给 AI。

### 在工具中处理错误

```python
from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType


class DivideParams(BaseModel):
    a: float = Field(description="被除数")
    b: float = Field(description="除数")


class DivideTool(CallableTool2[DivideParams]):
    """除法工具，演示错误处理。"""
    
    name: str = "divide"
    description: str = "计算两个数的商。"
    params: type[DivideParams] = DivideParams

    async def __call__(self, params: DivideParams) -> ToolReturnType:
        # 检查除数是否为零
        if params.b == 0:
            return ToolError(
                message="除数不能为零",
                brief="除零错误",
                output="无法执行除法运算，因为除数为零"
            )
        
        try:
            result = params.a / params.b
            return ToolOk(
                output=f"{params.a} ÷ {params.b} = {result}",
                brief="计算成功"
            )
        
        except Exception as e:
            return ToolError(
                message=f"计算失败: {str(e)}",
                brief="计算错误"
            )
```

### 处理工具结果中的错误

```python
import asyncio

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import ToolError, ToolOk
from kosong.tooling.simple import SimpleToolset


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    toolset += DivideTool()
    
    history = [
        Message(role="user", content="请计算 10 除以 0"),
    ]
    
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个数学助手",
        toolset=toolset,
        history=history,
    )
    
    # 检查工具执行结果
    tool_results = await result.tool_results()
    
    for tr in tool_results:
        if isinstance(tr.result, ToolError):
            print(f"❌ 工具错误: {tr.result.brief}")
            print(f"   详情: {tr.result.message}")
        elif isinstance(tr.result, ToolOk):
            print(f"✅ 工具成功: {tr.result.brief}")
            print(f"   输出: {tr.result.output}")


asyncio.run(main())
```

**预期输出**：

```text
❌ 工具错误: 除零错误
   详情: 除数不能为零
```

### 工具错误处理最佳实践

1. **永远不要抛出异常**：在工具的 `__call__` 方法中捕获所有异常并返回 `ToolError`
2. **提供清晰的错误信息**：
   - `message`：给 AI 的详细错误说明，帮助 AI 理解问题
   - `brief`：给用户的简短提示
   - `output`：可选的额外错误详情
3. **区分错误类型**：让 AI 知道是参数问题、权限问题还是系统问题
4. **记录日志**：对于重要错误，记录日志便于调试

```python
import logging

from pydantic import BaseModel

from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnType

logger = logging.getLogger(__name__)


class RobustToolParams(BaseModel):
    value: str


class RobustTool(CallableTool2[RobustToolParams]):
    """健壮的工具示例。"""
    
    name: str = "robust_tool"
    description: str = "一个健壮的工具"
    params: type[RobustToolParams] = RobustToolParams

    async def __call__(self, params: RobustToolParams) -> ToolReturnType:
        try:
            # 参数验证
            if not params.value:
                return ToolError(
                    message="参数 value 不能为空",
                    brief="参数错误"
                )
            
            # 执行操作
            result = await self._process(params.value)
            
            return ToolOk(
                output=result,
                brief="处理成功"
            )
        
        except ValueError as e:
            # 预期的错误，不需要记录堆栈
            logger.warning(f"参数验证失败: {e}")
            return ToolError(
                message=f"参数无效: {str(e)}",
                brief="参数错误"
            )
        
        except PermissionError as e:
            # 权限问题
            logger.error(f"权限不足: {e}")
            return ToolError(
                message=f"没有执行权限: {str(e)}",
                brief="权限不足"
            )
        
        except Exception as e:
            # 意外错误，记录完整堆栈
            logger.error(f"工具执行失败: {e}", exc_info=True)
            return ToolError(
                message=f"工具执行失败: {str(e)}",
                brief="执行失败"
            )
    
    async def _process(self, value: str) -> str:
        """实际的处理逻辑。"""
        return f"处理结果: {value}"
```

## 重试策略

对于临时性错误（如网络问题、超时、服务器错误），实现重试机制可以提高应用的可靠性。

### 简单重试

```python
import asyncio
from typing import TypeVar

import kosong
from kosong.chat_provider import APIConnectionError, APIStatusError, APITimeoutError

T = TypeVar("T")


async def retry_on_error(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> kosong.StepResult | None:
    """
    重试函数，支持指数退避。
    
    Args:
        func: 要执行的异步函数
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        
        except (APIConnectionError, APITimeoutError, APIStatusError) as e:
            last_error = e
            
            # 对于某些错误不重试
            if isinstance(e, APIStatusError):
                if e.status_code == 401:  # 认证失败
                    print(f"认证失败，不重试")
                    raise
                elif e.status_code < 500:  # 客户端错误
                    print(f"客户端错误 {e.status_code}，不重试")
                    raise
            
            if attempt < max_retries - 1:
                wait_time = delay * (backoff ** attempt)
                print(f"第 {attempt + 1} 次尝试失败: {e}")
                print(f"等待 {wait_time:.1f} 秒后重试...")
                await asyncio.sleep(wait_time)
            else:
                print(f"已达到最大重试次数 ({max_retries})")
    
    if last_error:
        raise last_error


async def main() -> None:
    from kosong.chat_provider.kimi import Kimi
    from kosong.message import Message
    from kosong.tooling.simple import SimpleToolset
    
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    history = [Message(role="user", content="你好")]
    
    # 使用重试机制
    result = await retry_on_error(
        lambda: kosong.step(
            chat_provider=kimi,
            system_prompt="你是一个助手",
            toolset=toolset,
            history=history,
        ),
        max_retries=3,
        delay=1.0,
        backoff=2.0,
    )
    
    if result:
        print(f"成功: {result.message.content}")


asyncio.run(main())
```

### 带重试的包装器

创建一个可复用的重试包装器：

```python
import asyncio
from functools import wraps
from typing import Callable, TypeVar

from kosong.chat_provider import APIConnectionError, APIStatusError, APITimeoutError

T = TypeVar("T")


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
):
    """
    装饰器：为异步函数添加重试功能。
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                
                except (APIConnectionError, APITimeoutError, APIStatusError) as e:
                    last_error = e
                    
                    # 不重试的情况
                    if isinstance(e, APIStatusError) and e.status_code < 500:
                        raise
                    
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        await asyncio.sleep(wait_time)
            
            if last_error:
                raise last_error
        
        return wrapper
    return decorator


# 使用装饰器
@with_retry(max_retries=3, delay=1.0, backoff=2.0)
async def call_api(chat_provider, system_prompt, toolset, history):
    """带重试的 API 调用。"""
    return await kosong.step(
        chat_provider=chat_provider,
        system_prompt=system_prompt,
        toolset=toolset,
        history=history,
    )
```

### 智能重试策略

根据错误类型采用不同的重试策略：

```python
import asyncio

from kosong.chat_provider import APIConnectionError, APIStatusError, APITimeoutError


class RetryStrategy:
    """智能重试策略。"""
    
    def __init__(self):
        self.max_retries = {
            APIConnectionError: 3,  # 连接错误重试 3 次
            APITimeoutError: 2,     # 超时重试 2 次
            APIStatusError: 1,      # 状态错误重试 1 次
        }
        self.delays = {
            APIConnectionError: 2.0,  # 连接错误等待 2 秒
            APITimeoutError: 5.0,     # 超时等待 5 秒
            APIStatusError: 1.0,      # 状态错误等待 1 秒
        }
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试。"""
        error_type = type(error)
        
        # 检查是否达到最大重试次数
        max_retries = self.max_retries.get(error_type, 0)
        if attempt >= max_retries:
            return False
        
        # 对于 APIStatusError，检查状态码
        if isinstance(error, APIStatusError):
            if error.status_code < 500:  # 客户端错误不重试
                return False
        
        return True
    
    def get_delay(self, error: Exception, attempt: int) -> float:
        """获取重试延迟时间。"""
        error_type = type(error)
        base_delay = self.delays.get(error_type, 1.0)
        
        # 指数退避
        return base_delay * (2 ** attempt)


async def smart_retry(func, strategy: RetryStrategy | None = None):
    """使用智能策略重试。"""
    if strategy is None:
        strategy = RetryStrategy()
    
    attempt = 0
    last_error = None
    
    while True:
        try:
            return await func()
        
        except Exception as e:
            last_error = e
            
            if not strategy.should_retry(e, attempt):
                raise
            
            delay = strategy.get_delay(e, attempt)
            print(f"第 {attempt + 1} 次尝试失败: {e}")
            print(f"等待 {delay:.1f} 秒后重试...")
            
            await asyncio.sleep(delay)
            attempt += 1


# 使用智能重试
async def main():
    import kosong
    from kosong.chat_provider.kimi import Kimi
    from kosong.message import Message
    from kosong.tooling.simple import SimpleToolset
    
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    history = [Message(role="user", content="你好")]
    
    result = await smart_retry(
        lambda: kosong.step(
            chat_provider=kimi,
            system_prompt="你是一个助手",
            toolset=toolset,
            history=history,
        )
    )
    
    print(f"成功: {result.message.content}")


asyncio.run(main())
```

## 优雅降级

当主要功能不可用时，优雅降级可以提供备选方案，确保应用仍能提供基本服务。

### 降级到备用模型

当主模型不可用时，切换到备用模型：

```python
import asyncio

import kosong
from kosong.chat_provider import ChatProviderError
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset


class FallbackChatProvider:
    """带降级功能的聊天提供商包装器。"""
    
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback
        self.using_fallback = False
    
    async def step(
        self,
        system_prompt: str,
        toolset,
        history,
    ) -> kosong.StepResult:
        """尝试使用主提供商，失败时降级到备用提供商。"""
        try:
            result = await kosong.step(
                chat_provider=self.primary,
                system_prompt=system_prompt,
                toolset=toolset,
                history=history,
            )
            self.using_fallback = False
            return result
        
        except ChatProviderError as e:
            print(f"⚠️ 主模型失败: {e}")
            print(f"🔄 切换到备用模型...")
            
            try:
                result = await kosong.step(
                    chat_provider=self.fallback,
                    system_prompt=system_prompt,
                    toolset=toolset,
                    history=history,
                )
                self.using_fallback = True
                return result
            
            except ChatProviderError as fallback_error:
                print(f"❌ 备用模型也失败: {fallback_error}")
                raise


async def main() -> None:
    # 配置主模型和备用模型
    primary = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="primary_api_key",
        model="kimi-k2-turbo-preview",
    )
    
    fallback = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="fallback_api_key",
        model="kimi-k1.5-chat",  # 更便宜的备用模型
    )
    
    provider = FallbackChatProvider(primary, fallback)
    
    toolset = SimpleToolset()
    history = [Message(role="user", content="你好")]
    
    result = await provider.step(
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
    
    if provider.using_fallback:
        print("⚠️ 使用了备用模型")
    
    print(f"响应: {result.message.content}")


asyncio.run(main())
```

### 降级到简化功能

当完整功能不可用时，提供简化版本：

```python
import asyncio

import kosong
from kosong.chat_provider import ChatProviderError
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset


async def full_featured_step(
    chat_provider,
    system_prompt: str,
    toolset,
    history,
) -> kosong.StepResult | None:
    """完整功能版本（带工具调用）。"""
    try:
        return await kosong.step(
            chat_provider=chat_provider,
            system_prompt=system_prompt,
            toolset=toolset,
            history=history,
        )
    except ChatProviderError as e:
        print(f"完整功能失败: {e}")
        return None


async def simplified_step(
    chat_provider,
    system_prompt: str,
    history,
) -> kosong.StepResult | None:
    """简化版本（不使用工具）。"""
    try:
        # 使用空工具集
        empty_toolset = SimpleToolset()
        return await kosong.step(
            chat_provider=chat_provider,
            system_prompt=system_prompt + "\n注意：当前工具不可用，请直接回答。",
            toolset=empty_toolset,
            history=history,
        )
    except ChatProviderError as e:
        print(f"简化功能也失败: {e}")
        return None


async def graceful_step(
    chat_provider,
    system_prompt: str,
    toolset,
    history,
) -> kosong.StepResult | None:
    """优雅降级的 step 函数。"""
    # 首先尝试完整功能
    result = await full_featured_step(
        chat_provider,
        system_prompt,
        toolset,
        history,
    )
    
    if result:
        return result
    
    # 降级到简化功能
    print("🔄 降级到简化模式（不使用工具）")
    result = await simplified_step(
        chat_provider,
        system_prompt,
        history,
    )
    
    return result


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    # 添加一些工具...
    
    history = [Message(role="user", content="帮我查询天气")]
    
    result = await graceful_step(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
    )
    
    if result:
        print(f"响应: {result.message.content}")
    else:
        print("所有尝试都失败了")


asyncio.run(main())
```


### 缓存和离线模式

使用缓存提供离线降级：

```python
import asyncio
import hashlib
import json
from pathlib import Path

import kosong
from kosong.chat_provider import ChatProviderError
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset


class CachedChatProvider:
    """带缓存的聊天提供商。"""
    
    def __init__(self, chat_provider, cache_dir: str = ".cache"):
        self.chat_provider = chat_provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, system_prompt: str, history) -> str:
        """生成缓存键。"""
        content = json.dumps({
            "system_prompt": system_prompt,
            "history": [
                {"role": msg.role, "content": str(msg.content)}
                for msg in history
            ],
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径。"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_cache(self, cache_key: str) -> str | None:
        """加载缓存。"""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
        return None
    
    def _save_cache(self, cache_key: str, content: str) -> None:
        """保存缓存。"""
        cache_path = self._get_cache_path(cache_key)
        cache_path.write_text(content, encoding="utf-8")
    
    async def step(
        self,
        system_prompt: str,
        toolset,
        history,
    ) -> kosong.StepResult | Message | None:
        """带缓存的 step 调用。"""
        cache_key = self._get_cache_key(system_prompt, history)
        
        try:
            # 尝试调用 API
            result = await kosong.step(
                chat_provider=self.chat_provider,
                system_prompt=system_prompt,
                toolset=toolset,
                history=history,
            )
            
            # 保存到缓存
            if isinstance(result.message.content, str):
                self._save_cache(cache_key, result.message.content)
            
            return result
        
        except ChatProviderError as e:
            print(f"⚠️ API 调用失败: {e}")
            
            # 尝试从缓存加载
            cached_content = self._load_cache(cache_key)
            if cached_content:
                print("📦 使用缓存的响应")
                return Message(role="assistant", content=cached_content)
            
            print("❌ 没有可用的缓存")
            return None


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    provider = CachedChatProvider(kimi, cache_dir=".chat_cache")
    
    toolset = SimpleToolset()
    history = [Message(role="user", content="什么是 Python？")]
    
    result = await provider.step(
        system_prompt="你是一个编程助手",
        toolset=toolset,
        history=history,
    )
    
    if result:
        if isinstance(result, Message):
            print(f"缓存响应: {result.content}")
        else:
            print(f"API 响应: {result.message.content}")
    else:
        print("无法获取响应")


asyncio.run(main())
```

### 提供默认响应

当所有尝试都失败时，返回有用的默认响应：

```python
import asyncio

import kosong
from kosong.chat_provider import ChatProviderError
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset


async def step_with_default(
    chat_provider,
    system_prompt: str,
    toolset,
    history,
    default_message: str = "抱歉，我现在无法处理您的请求。请稍后再试。",
) -> Message:
    """带默认响应的 step 函数。"""
    try:
        result = await kosong.step(
            chat_provider=chat_provider,
            system_prompt=system_prompt,
            toolset=toolset,
            history=history,
        )
        return result.message
    
    except ChatProviderError as e:
        print(f"⚠️ 请求失败: {e}")
        print(f"📝 返回默认响应")
        
        # 返回默认消息
        return Message(
            role="assistant",
            content=default_message,
        )


async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_api_key_here",
        model="kimi-k2-turbo-preview",
    )
    
    toolset = SimpleToolset()
    history = [Message(role="user", content="你好")]
    
    message = await step_with_default(
        chat_provider=kimi,
        system_prompt="你是一个助手",
        toolset=toolset,
        history=history,
        default_message="抱歉，服务暂时不可用。我们正在努力修复。",
    )
    
    print(f"响应: {message.content}")


asyncio.run(main())
```

## 完整示例：健壮的 Agent

下面是一个综合示例，展示如何构建一个健壮的 Agent，包含错误处理、重试和降级：

```python
import asyncio
import logging
from typing import Literal

import kosong
from kosong.chat_provider import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    ChatProviderError,
)
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobustAgent:
    """健壮的 AI Agent，具备完善的错误处理能力。"""
    
    def __init__(
        self,
        chat_provider,
        fallback_provider=None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.chat_provider = chat_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_count = 0
        self.success_count = 0
    
    async def chat(
        self,
        system_prompt: str,
        toolset,
        history: list[Message],
    ) -> Message | None:
        """
        执行一次对话，包含完整的错误处理。
        
        Returns:
            Message 对象，如果所有尝试都失败则返回 None
        """
        # 首先尝试主提供商（带重试）
        result = await self._try_with_retry(
            self.chat_provider,
            system_prompt,
            toolset,
            history,
        )
        
        if result:
            self.success_count += 1
            return result.message
        
        # 如果有备用提供商，尝试降级
        if self.fallback_provider:
            logger.warning("主提供商失败，尝试备用提供商")
            result = await self._try_with_retry(
                self.fallback_provider,
                system_prompt,
                toolset,
                history,
            )
            
            if result:
                self.success_count += 1
                logger.info("备用提供商成功")
                return result.message
        
        # 所有尝试都失败
        self.error_count += 1
        logger.error("所有尝试都失败")
        return None
    
    async def _try_with_retry(
        self,
        chat_provider,
        system_prompt: str,
        toolset,
        history,
    ) -> kosong.StepResult | None:
        """带重试的单次尝试。"""
        for attempt in range(self.max_retries):
            try:
                result = await kosong.step(
                    chat_provider=chat_provider,
                    system_prompt=system_prompt,
                    toolset=toolset,
                    history=history,
                )
                return result
            
            except APIConnectionError as e:
                logger.warning(f"连接失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
            
            except APITimeoutError as e:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
            
            except APIStatusError as e:
                if e.status_code == 429:
                    # 速率限制，等待更长时间
                    logger.warning(f"速率限制 (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (3 ** attempt))
                elif e.status_code >= 500:
                    # 服务器错误，可以重试
                    logger.warning(f"服务器错误 {e.status_code} (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    # 客户端错误，不重试
                    logger.error(f"客户端错误 {e.status_code}: {e}")
                    break
            
            except ChatProviderError as e:
                logger.error(f"未知错误: {e}")
                break
        
        return None
    
    def get_stats(self) -> dict:
        """获取统计信息。"""
        total = self.success_count + self.error_count
        success_rate = (
            self.success_count / total * 100
            if total > 0
            else 0
        )
        
        return {
            "success_count": self.success_count,
            "error_count": self.error_count,
            "total": total,
            "success_rate": f"{success_rate:.1f}%",
        }


async def main() -> None:
    # 配置主提供商和备用提供商
    primary = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="primary_api_key",
        model="kimi-k2-turbo-preview",
    )
    
    fallback = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="fallback_api_key",
        model="kimi-k1.5-chat",
    )
    
    # 创建健壮的 Agent
    agent = RobustAgent(
        chat_provider=primary,
        fallback_provider=fallback,
        max_retries=3,
        retry_delay=1.0,
    )
    
    toolset = SimpleToolset()
    
    # 进行多轮对话
    conversations = [
        "你好，介绍一下你自己",
        "Python 有什么特点？",
        "如何学习编程？",
    ]
    
    for user_message in conversations:
        print(f"\n用户: {user_message}")
        
        history = [Message(role="user", content=user_message)]
        
        response = await agent.chat(
            system_prompt="你是一个友好的编程助手",
            toolset=toolset,
            history=history,
        )
        
        if response:
            print(f"助手: {response.content}")
        else:
            print("助手: [无法获取响应]")
    
    # 显示统计信息
    print("\n" + "=" * 50)
    print("统计信息:")
    stats = agent.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


asyncio.run(main())
```

## 最佳实践总结

1. **分层处理错误**：
   - 区分致命错误、可重试错误和可忽略错误
   - 对不同类型的错误采取不同的处理策略

2. **实现重试机制**：
   - 使用指数退避避免过度重试
   - 为不同错误类型设置不同的重试次数
   - 对客户端错误（4xx）不要重试

3. **提供降级方案**：
   - 准备备用模型或服务
   - 简化功能而不是完全失败
   - 使用缓存提供离线能力

4. **记录和监控**：
   - 记录所有错误和重试
   - 收集统计信息
   - 设置告警阈值

5. **用户体验**：
   - 提供清晰的错误信息
   - 避免让用户看到技术细节
   - 在降级时告知用户

6. **工具错误处理**：
   - 永远不要在工具中抛出异常
   - 返回清晰的 ToolError
   - 区分参数错误和运行时错误

## 相关资源

- [API 参考 - ChatProvider](../api-reference/chat-provider.md)：了解所有异常类型
- [API 参考 - Tooling](../api-reference/tooling.md)：了解工具错误处理
- [自定义工具指南](./custom-tools.md)：学习如何创建健壮的工具
- [多轮对话指南](./multi-turn-conversation.md)：在对话中处理错误

## 下一步

- 学习如何[实现流式输出](./streaming-output.md)
- 了解如何[构建多轮对话](./multi-turn-conversation.md)
- 探索[高级特性](../advanced/README.md)
