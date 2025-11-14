---
title: kosong.message
description: 消息和内容部分的数据模型
version: 0.23.0
last_updated: 2025-01-15
---

# kosong.message

> 定义对话消息和内容部分的数据模型，支持文本、思考、图像、音频和工具调用。

`kosong.message` 模块提供了构建 LLM 对话所需的核心数据结构。`Message` 类表示对话中的一条消息，而 `ContentPart` 及其子类用于表示消息内容的不同类型（文本、图像、音频等）。

## Message 类

`Message` 是对话中的一条消息，包含角色、内容和可选的工具调用信息。

### 类定义

```python
class Message(BaseModel):
    """A message in a conversation."""

    role: Literal["system", "user", "assistant", "tool"]
    """消息发送者的角色"""

    name: str | None = None
    """消息发送者的名称（可选）"""

    content: str | list[ContentPart]
    """消息的内容，可以是纯文本字符串或内容部分列表"""

    tool_calls: list[ToolCall] | None = None
    """助手在此消息中请求的工具调用列表"""

    tool_call_id: str | None = None
    """如果此消息是工具响应，则为对应的工具调用 ID"""

    partial: bool | None = None
    """标记此消息是否为部分消息（流式传输中）"""
```

### 角色说明

- **system**: 系统消息，用于设定 AI 的行为规范和角色
- **user**: 用户消息，表示用户的输入
- **assistant**: 助手消息，表示 AI 的响应
- **tool**: 工具响应消息，包含工具执行的结果

### 使用示例

#### 示例 1：创建纯文本消息

```python
from kosong.message import Message

# 用户消息
user_msg = Message(role="user", content="你好，世界！")
print(user_msg.model_dump(exclude_none=True))
# 输出: {'role': 'user', 'content': '你好，世界！'}

# 系统消息
system_msg = Message(role="system", content="你是一个友好的助手。")

# 助手消息
assistant_msg = Message(role="assistant", content="你好！有什么我可以帮助你的吗？")
```

#### 示例 2：创建多部分内容消息

```python
from kosong.message import Message, TextPart, ImageURLPart

# 包含文本和图像的消息
message = Message(
    role="user",
    content=[
        TextPart(text="这张图片里有什么？"),
        ImageURLPart(
            image_url=ImageURLPart.ImageURL(
                url="https://example.com/image.png"
            )
        ),
    ],
)
```

#### 示例 3：带工具调用的消息

```python
from kosong.message import Message, TextPart, ToolCall

# 助手请求调用工具
message = Message(
    role="assistant",
    content=[TextPart(text="让我帮你查询天气。")],
    tool_calls=[
        ToolCall(
            id="call_123",
            function=ToolCall.FunctionBody(
                name="get_weather",
                arguments='{"city": "北京"}'
            )
        )
    ],
)
```

#### 示例 4：工具响应消息

```python
from kosong.message import Message

# 工具执行结果
tool_response = Message(
    role="tool",
    tool_call_id="call_123",
    content="北京：晴天，温度 25°C",
)
```


## ContentPart 类

`ContentPart` 是消息内容部分的抽象基类，所有具体的内容类型都继承自它。

### 类定义

```python
class ContentPart(BaseModel, ABC, MergeableMixin):
    """A part of a message content."""

    type: str
    """内容部分的类型标识"""
```

### 子类

Kosong 提供了以下 `ContentPart` 子类：

- **TextPart**: 文本内容
- **ThinkPart**: 思考内容（用于推理过程）
- **ImageURLPart**: 图像 URL 内容
- **AudioURLPart**: 音频 URL 内容

### 合并机制

`ContentPart` 实现了 `MergeableMixin`，支持在流式传输中合并相邻的内容部分：

```python
class MergeableMixin:
    def merge_in_place(self, other: Any) -> bool:
        """将另一个部分合并到当前部分。如果合并成功返回 True。"""
        return False
```

## TextPart 类

表示文本内容的部分。

### 类定义

```python
class TextPart(ContentPart):
    """文本内容部分"""

    type: str = "text"
    text: str
    """文本内容"""
```

### 使用示例

```python
from kosong.message import TextPart, Message

# 创建文本部分
text_part = TextPart(text="Hello, world!")
print(text_part.model_dump())
# 输出: {'type': 'text', 'text': 'Hello, world!'}

# 在消息中使用
message = Message(
    role="user",
    content=[
        TextPart(text="第一段文本。"),
        TextPart(text="第二段文本。"),
    ],
)
```

### 合并行为

相邻的 `TextPart` 可以合并：

```python
part1 = TextPart(text="Hello, ")
part2 = TextPart(text="world!")

# 合并
success = part1.merge_in_place(part2)
print(success)  # True
print(part1.text)  # "Hello, world!"
```

## ThinkPart 类

表示 AI 的思考过程内容，通常用于展示推理步骤。

### 类定义

```python
class ThinkPart(ContentPart):
    """思考内容部分"""

    type: str = "think"
    think: str
    """思考内容"""
    
    encrypted: str | None = None
    """加密的思考内容或签名"""
```

### 使用示例

```python
from kosong.message import ThinkPart, Message

# 创建思考部分
think_part = ThinkPart(think="我需要先分析这个问题...")
print(think_part.model_dump())
# 输出: {'type': 'think', 'think': '我需要先分析这个问题...', 'encrypted': None}

# 在消息中使用
message = Message(
    role="assistant",
    content=[
        ThinkPart(think="首先，我需要理解用户的需求。"),
        TextPart(text="让我帮你解决这个问题。"),
    ],
)
```

### 合并行为

`ThinkPart` 可以合并，但如果已有加密内容则不能合并：

```python
part1 = ThinkPart(think="第一步：")
part2 = ThinkPart(think="分析问题")

# 合并成功
success = part1.merge_in_place(part2)
print(success)  # True
print(part1.think)  # "第一步：分析问题"

# 有加密内容时不能合并
part3 = ThinkPart(think="思考", encrypted="signature")
part4 = ThinkPart(think="更多")
success = part3.merge_in_place(part4)
print(success)  # False
```


## ImageURLPart 类

表示图像 URL 内容，支持远程 URL 和 Data URI。

### 类定义

```python
class ImageURLPart(ContentPart):
    """图像 URL 内容部分"""

    class ImageURL(BaseModel):
        """图像 URL 载荷"""

        url: str
        """图像的 URL，可以是 data URI 格式如 `data:image/png;base64,...`"""
        
        id: str | None = None
        """图像的 ID，用于让 LLM 区分不同的图像"""

    type: str = "image_url"
    image_url: ImageURL
```

### 使用示例

#### 示例 1：使用远程图像 URL

```python
from kosong.message import ImageURLPart, Message

# 创建图像部分
image_part = ImageURLPart(
    image_url=ImageURLPart.ImageURL(
        url="https://example.com/image.png"
    )
)

print(image_part.model_dump())
# 输出: {'type': 'image_url', 'image_url': {'url': 'https://example.com/image.png', 'id': None}}

# 在消息中使用
message = Message(
    role="user",
    content=[
        TextPart(text="请分析这张图片："),
        image_part,
    ],
)
```

#### 示例 2：使用 Data URI

```python
import base64
from kosong.message import ImageURLPart

# 读取图像文件并转换为 base64
with open("image.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# 创建 Data URI
data_uri = f"data:image/png;base64,{image_data}"

image_part = ImageURLPart(
    image_url=ImageURLPart.ImageURL(url=data_uri)
)
```

#### 示例 3：使用图像 ID 区分多张图片

```python
from kosong.message import ImageURLPart, TextPart, Message

message = Message(
    role="user",
    content=[
        TextPart(text="比较这两张图片的差异："),
        ImageURLPart(
            image_url=ImageURLPart.ImageURL(
                url="https://example.com/image1.png",
                id="image_1"
            )
        ),
        ImageURLPart(
            image_url=ImageURLPart.ImageURL(
                url="https://example.com/image2.png",
                id="image_2"
            )
        ),
    ],
)
```

## AudioURLPart 类

表示音频 URL 内容，支持远程 URL 和 Data URI。

### 类定义

```python
class AudioURLPart(ContentPart):
    """音频 URL 内容部分"""

    class AudioURL(BaseModel):
        """音频 URL 载荷"""

        url: str
        """音频的 URL，可以是 data URI 格式如 `data:audio/aac;base64,...`"""
        
        id: str | None = None
        """音频的 ID，用于让 LLM 区分不同的音频"""

    type: str = "audio_url"
    audio_url: AudioURL
```

### 使用示例

#### 示例 1：使用远程音频 URL

```python
from kosong.message import AudioURLPart, Message

# 创建音频部分
audio_part = AudioURLPart(
    audio_url=AudioURLPart.AudioURL(
        url="https://example.com/audio.mp3"
    )
)

print(audio_part.model_dump())
# 输出: {'type': 'audio_url', 'audio_url': {'url': 'https://example.com/audio.mp3', 'id': None}}

# 在消息中使用
message = Message(
    role="user",
    content=[
        TextPart(text="请转录这段音频："),
        audio_part,
    ],
)
```

#### 示例 2：使用 Data URI

```python
import base64
from kosong.message import AudioURLPart

# 读取音频文件并转换为 base64
with open("audio.mp3", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode()

# 创建 Data URI
data_uri = f"data:audio/mpeg;base64,{audio_data}"

audio_part = AudioURLPart(
    audio_url=AudioURLPart.AudioURL(url=data_uri)
)
```

#### 示例 3：使用音频 ID

```python
from kosong.message import AudioURLPart, TextPart, Message

message = Message(
    role="user",
    content=[
        TextPart(text="比较这两段音频的说话人："),
        AudioURLPart(
            audio_url=AudioURLPart.AudioURL(
                url="https://example.com/speaker1.mp3",
                id="speaker_1"
            )
        ),
        AudioURLPart(
            audio_url=AudioURLPart.AudioURL(
                url="https://example.com/speaker2.mp3",
                id="speaker_2"
            )
        ),
    ],
)
```


## ToolCall 类

表示助手请求的工具调用。

### 类定义

```python
class ToolCall(BaseModel, MergeableMixin):
    """助手请求的工具调用"""

    class FunctionBody(BaseModel):
        """工具调用函数体"""

        name: str
        """要调用的工具名称"""
        
        arguments: str | None
        """工具调用的参数，JSON 字符串格式"""

    type: Literal["function"] = "function"
    """工具调用类型，目前仅支持 'function'"""

    id: str
    """工具调用的唯一 ID"""
    
    function: FunctionBody
    """工具调用的函数体"""
```

### 使用示例

#### 示例 1：创建工具调用

```python
from kosong.message import ToolCall

# 创建工具调用
tool_call = ToolCall(
    id="call_123",
    function=ToolCall.FunctionBody(
        name="get_weather",
        arguments='{"city": "北京"}'
    )
)

print(tool_call.model_dump())
# 输出: {
#     'type': 'function',
#     'id': 'call_123',
#     'function': {
#         'name': 'get_weather',
#         'arguments': '{"city": "北京"}'
#     }
# }
```

#### 示例 2：在助手消息中使用

```python
from kosong.message import Message, TextPart, ToolCall

# 助手请求调用多个工具
message = Message(
    role="assistant",
    content=[TextPart(text="让我帮你查询天气和时间。")],
    tool_calls=[
        ToolCall(
            id="call_1",
            function=ToolCall.FunctionBody(
                name="get_weather",
                arguments='{"city": "北京"}'
            )
        ),
        ToolCall(
            id="call_2",
            function=ToolCall.FunctionBody(
                name="get_time",
                arguments='{"timezone": "Asia/Shanghai"}'
            )
        ),
    ],
)
```

#### 示例 3：处理工具调用参数

```python
import json
from kosong.message import ToolCall

tool_call = ToolCall(
    id="call_456",
    function=ToolCall.FunctionBody(
        name="calculate",
        arguments='{"expression": "2 + 3"}'
    )
)

# 解析参数
if tool_call.function.arguments:
    params = json.loads(tool_call.function.arguments)
    print(params)  # {'expression': '2 + 3'}
```

### 合并行为

`ToolCall` 支持与 `ToolCallPart` 合并，用于流式传输中逐步构建完整的工具调用：

```python
from kosong.message import ToolCall, ToolCallPart

# 初始工具调用（参数为空）
tool_call = ToolCall(
    id="call_789",
    function=ToolCall.FunctionBody(
        name="search",
        arguments=None
    )
)

# 逐步添加参数片段
part1 = ToolCallPart(arguments_part='{"query": ')
part2 = ToolCallPart(arguments_part='"Python"}')

tool_call.merge_in_place(part1)
print(tool_call.function.arguments)  # '{"query": '

tool_call.merge_in_place(part2)
print(tool_call.function.arguments)  # '{"query": "Python"}'
```

## ToolCallPart 类

表示工具调用的一个片段，用于流式传输。

### 类定义

```python
class ToolCallPart(BaseModel, MergeableMixin):
    """工具调用的一个部分"""

    arguments_part: str | None = None
    """工具调用参数的一个片段"""
```

### 使用示例

```python
from kosong.message import ToolCallPart

# 创建工具调用片段
part = ToolCallPart(arguments_part='{"city": ')
print(part.model_dump())
# 输出: {'arguments_part': '{"city": '}

# 合并片段
part1 = ToolCallPart(arguments_part='{"city": ')
part2 = ToolCallPart(arguments_part='"北京"}')

success = part1.merge_in_place(part2)
print(success)  # True
print(part1.arguments_part)  # '{"city": "北京"}'
```

### 在流式处理中的应用

`ToolCallPart` 主要用于内部流式处理，通常不需要直接创建：

```python
from kosong import generate
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message, ToolCallPart

async def on_message_part(part):
    if isinstance(part, ToolCallPart):
        print(f"接收到工具调用片段: {part.arguments_part}")

kimi = Kimi(...)
result = await generate(
    chat_provider=kimi,
    system_prompt="你是一个助手。",
    tools=[...],
    history=[Message(role="user", content="查询天气")],
    on_message_part=on_message_part,
)
```


## 序列化和反序列化

所有消息和内容部分类都基于 Pydantic，支持方便的序列化和反序列化。

### 序列化为字典

```python
from kosong.message import Message, TextPart, ImageURLPart

message = Message(
    role="user",
    content=[
        TextPart(text="这是什么？"),
        ImageURLPart(
            image_url=ImageURLPart.ImageURL(url="https://example.com/img.png")
        ),
    ],
)

# 序列化（排除 None 值）
data = message.model_dump(exclude_none=True)
print(data)
# 输出: {
#     'role': 'user',
#     'content': [
#         {'type': 'text', 'text': '这是什么？'},
#         {'type': 'image_url', 'image_url': {'url': 'https://example.com/img.png'}}
#     ]
# }
```

### 从字典反序列化

```python
from kosong.message import Message

# 从字典创建消息
data = {
    'role': 'assistant',
    'content': [
        {'type': 'text', 'text': 'Hello!'}
    ],
    'tool_calls': [
        {
            'type': 'function',
            'id': 'call_123',
            'function': {
                'name': 'get_weather',
                'arguments': '{"city": "北京"}'
            }
        }
    ]
}

message = Message.model_validate(data)
print(message.role)  # 'assistant'
print(len(message.tool_calls))  # 1
```

### JSON 序列化

```python
import json
from kosong.message import Message, TextPart

message = Message(
    role="user",
    content=[TextPart(text="你好")]
)

# 转换为 JSON 字符串
json_str = message.model_dump_json(exclude_none=True)
print(json_str)
# 输出: '{"role":"user","content":[{"type":"text","text":"你好"}]}'

# 从 JSON 字符串解析
message2 = Message.model_validate_json(json_str)
print(message2 == message)  # True
```

## 内容类型自动识别

`ContentPart` 实现了智能的类型识别机制，可以根据 `type` 字段自动选择正确的子类：

```python
from kosong.message import Message

# 自动识别不同类型的内容部分
data = {
    'role': 'user',
    'content': [
        {'type': 'text', 'text': '文本'},
        {'type': 'think', 'think': '思考'},
        {'type': 'image_url', 'image_url': {'url': 'https://example.com/img.png'}},
        {'type': 'audio_url', 'audio_url': {'url': 'https://example.com/audio.mp3'}},
    ]
}

message = Message.model_validate(data)

# 每个内容部分都被正确解析为对应的类型
from kosong.message import TextPart, ThinkPart, ImageURLPart, AudioURLPart

assert isinstance(message.content[0], TextPart)
assert isinstance(message.content[1], ThinkPart)
assert isinstance(message.content[2], ImageURLPart)
assert isinstance(message.content[3], AudioURLPart)
```

## 实用模式

### 模式 1：构建多模态对话

```python
from kosong.message import Message, TextPart, ImageURLPart, AudioURLPart

# 用户发送包含文本、图像和音频的消息
user_message = Message(
    role="user",
    content=[
        TextPart(text="请分析这张图片和这段音频："),
        ImageURLPart(
            image_url=ImageURLPart.ImageURL(url="https://example.com/photo.jpg")
        ),
        AudioURLPart(
            audio_url=AudioURLPart.AudioURL(url="https://example.com/voice.mp3")
        ),
    ],
)
```

### 模式 2：处理工具调用流程

```python
from kosong.message import Message, TextPart, ToolCall

# 1. 用户请求
user_msg = Message(role="user", content="北京今天天气怎么样？")

# 2. 助手请求调用工具
assistant_msg = Message(
    role="assistant",
    content=[TextPart(text="让我查询一下。")],
    tool_calls=[
        ToolCall(
            id="call_123",
            function=ToolCall.FunctionBody(
                name="get_weather",
                arguments='{"city": "北京"}'
            )
        )
    ],
)

# 3. 工具返回结果
tool_msg = Message(
    role="tool",
    tool_call_id="call_123",
    content="北京：晴天，25°C",
)

# 4. 助手基于工具结果回复
final_msg = Message(
    role="assistant",
    content="北京今天是晴天，温度 25°C。"
)

# 完整对话历史
history = [user_msg, assistant_msg, tool_msg, final_msg]
```

### 模式 3：空内容消息（仅工具调用）

```python
from kosong.message import Message, ToolCall

# 某些情况下，助手可能只调用工具而不返回文本
message = Message(
    role="assistant",
    content="",  # 空内容
    tool_calls=[
        ToolCall(
            id="call_456",
            function=ToolCall.FunctionBody(
                name="execute_action",
                arguments='{"action": "save"}'
            )
        )
    ],
)

# 序列化时空内容会变为 None
data = message.model_dump(exclude_none=True)
print(data['content'])  # None
```

### 模式 4：带名称的消息

```python
from kosong.message import Message

# 在多用户对话中使用名称区分
message1 = Message(
    role="user",
    name="Alice",
    content="我觉得这个方案不错。"
)

message2 = Message(
    role="user",
    name="Bob",
    content="我有不同的看法。"
)
```


## 注意事项

### 内容字段的灵活性

`Message.content` 可以是字符串或 `ContentPart` 列表：

```python
# 纯文本（推荐用于简单消息）
msg1 = Message(role="user", content="你好")

# ContentPart 列表（用于多模态或复杂内容）
msg2 = Message(
    role="user",
    content=[TextPart(text="你好")]
)

# 两者在功能上等价，但序列化结果不同
print(msg1.model_dump()['content'])  # "你好"
print(msg2.model_dump()['content'])  # [{'type': 'text', 'text': '你好'}]
```

### 空内容的处理

空字符串内容在序列化时会变为 `None`：

```python
from kosong.message import Message, ToolCall

message = Message(
    role="assistant",
    content="",
    tool_calls=[
        ToolCall(
            id="call_1",
            function=ToolCall.FunctionBody(name="tool", arguments="{}")
        )
    ],
)

data = message.model_dump(exclude_none=True)
print(data['content'])  # None（而不是 ""）
```

### 工具调用 ID 的唯一性

每个 `ToolCall` 的 `id` 必须是唯一的，以便正确匹配工具响应：

```python
# ✅ 正确：每个工具调用有唯一 ID
tool_calls = [
    ToolCall(id="call_1", function=...),
    ToolCall(id="call_2", function=...),
]

# ❌ 错误：重复的 ID 会导致混淆
tool_calls = [
    ToolCall(id="call_1", function=...),
    ToolCall(id="call_1", function=...),  # 重复！
]
```

### 工具响应必须匹配工具调用

工具响应消息的 `tool_call_id` 必须与对应的 `ToolCall.id` 匹配：

```python
# 助手的工具调用
assistant_msg = Message(
    role="assistant",
    content="",
    tool_calls=[
        ToolCall(id="call_abc", function=...)
    ],
)

# 对应的工具响应
tool_msg = Message(
    role="tool",
    tool_call_id="call_abc",  # 必须匹配
    content="工具执行结果",
)
```

### 角色顺序约定

虽然 Kosong 不强制要求，但遵循以下顺序有助于保持对话的清晰性：

1. **system** 消息通常在对话开始
2. **user** 和 **assistant** 消息交替出现
3. **tool** 消息紧跟在包含 `tool_calls` 的 **assistant** 消息之后

```python
# 推荐的消息顺序
history = [
    Message(role="system", content="系统提示"),
    Message(role="user", content="用户问题"),
    Message(role="assistant", content="", tool_calls=[...]),
    Message(role="tool", tool_call_id="...", content="工具结果"),
    Message(role="assistant", content="基于工具结果的回复"),
]
```

### Data URI 的大小限制

使用 Data URI 嵌入图像或音频时，注意 API 提供商可能有大小限制：

```python
import base64

# 检查文件大小
with open("large_image.png", "rb") as f:
    data = f.read()
    size_mb = len(data) / (1024 * 1024)
    
    if size_mb > 10:  # 假设限制为 10MB
        print("文件太大，考虑使用远程 URL")
    else:
        # 转换为 Data URI
        b64_data = base64.b64encode(data).decode()
        data_uri = f"data:image/png;base64,{b64_data}"
```

### 部分消息标记

`partial` 字段用于标记流式传输中的部分消息，通常由内部机制管理：

```python
# 流式传输中的部分消息
partial_msg = Message(
    role="assistant",
    content=[TextPart(text="正在生成")],
    partial=True,
)

# 完整消息
complete_msg = Message(
    role="assistant",
    content=[TextPart(text="正在生成完整的响应。")],
    partial=False,  # 或省略（默认为 None）
)
```

## 相关 API

- [generate](./generate.md) - 使用 Message 生成 LLM 响应
- [step](./step.md) - 执行包含工具调用的 Agent 步骤
- [ChatProvider](./chat-provider.md) - 处理 Message 的聊天提供者
- [Tooling](./tooling.md) - 工具调用相关的类和函数

## 类型提示

在使用 Message 时，可以利用类型提示提高代码质量：

```python
from typing import Sequence
from kosong.message import Message, ContentPart, TextPart

def process_messages(messages: Sequence[Message]) -> None:
    """处理消息列表"""
    for msg in messages:
        if isinstance(msg.content, str):
            print(f"纯文本: {msg.content}")
        else:
            # msg.content 是 list[ContentPart]
            for part in msg.content:
                if isinstance(part, TextPart):
                    print(f"文本部分: {part.text}")

def create_user_message(text: str) -> Message:
    """创建用户消息"""
    return Message(role="user", content=text)
```

---

_文档版本: v0.23.0 | 最后更新: 2025-01-15_
