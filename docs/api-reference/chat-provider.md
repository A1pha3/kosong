---
title: kosong.chat_provider
description: ChatProvider 协议和相关类型定义
version: 0.23.0
last_updated: 2025-01-15
---

# kosong.chat_provider

> 定义 ChatProvider 协议和流式消息接口，支持多种 LLM 提供商的统一访问。

`kosong.chat_provider` 模块提供了与 LLM 提供商交互的核心接口。通过 `ChatProvider` 协议，Kosong 可以支持多种不同的 LLM 服务（如 Kimi、OpenAI 等），同时保持统一的 API。

## ChatProvider 协议

`ChatProvider` 是所有聊天提供者必须实现的协议接口。

### 协议定义

```python
@runtime_checkable
class ChatProvider(Protocol):
    """聊天提供者的接口"""

    name: str
    """聊天提供者的名称"""

    @property
    def model_name(self) -> str:
        """使用的模型名称"""
        ...

    async def generate(
        self,
        system_prompt: str,
        tools: Sequence[Tool],
        history: Sequence[Message],
    ) -> StreamedMessage:
        """
        基于给定的系统提示、工具和历史生成新消息。

        异常:
            APIConnectionError: API 连接失败时抛出
            APITimeoutError: API 请求超时时抛出
            APIStatusError: API 返回 4xx 或 5xx 状态码时抛出
            ChatProviderError: 其他已识别的聊天提供者错误
        """
        ...

    def with_thinking(self, effort: ThinkingEffort) -> Self:
        """
        返回配置了指定思考强度的副本。
        如果聊天提供者不支持思考功能，则返回自身的副本。
        """
        ...
```

### 属性说明

- **name** (`str`): 聊天提供者的标识名称，如 `"kimi"`、`"openai"` 等
- **model_name** (`str`): 当前使用的模型名称，如 `"kimi-k2-turbo-preview"`

### 方法说明

#### generate()

生成一条新的 LLM 响应消息。

**参数：**
- **system_prompt** (`str`): 系统提示词
- **tools** (`Sequence[Tool]`): 可用的工具列表
- **history** (`Sequence[Message]`): 对话历史

**返回：** `StreamedMessage` - 流式消息对象

**异常：**
- `APIConnectionError`: 网络连接失败
- `APITimeoutError`: 请求超时
- `APIStatusError`: API 返回错误状态码
- `ChatProviderError`: 其他提供者相关错误

#### with_thinking()

配置思考强度并返回新的提供者实例。

**参数：**
- **effort** (`ThinkingEffort`): 思考强度级别，可选值：`"off"`, `"low"`, `"medium"`, `"high"`

**返回：** `Self` - 配置后的新实例

