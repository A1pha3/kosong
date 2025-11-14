---
title: kosong.tooling
description: 工具定义和工具集管理
version: 0.23.0
last_updated: 2025-01-15
---

# kosong.tooling

> 定义可被 LLM 调用的工具，以及管理工具调用的工具集。

`kosong.tooling` 模块提供了定义和管理 LLM 工具的核心功能。`Tool` 类定义工具的基本结构，`CallableTool` 和 `CallableTool2` 抽象类用于创建可调用的工具实现，`Toolset` 协议定义工具集接口，`SimpleToolset` 提供了一个简单的工具集实现。

## Tool 类

`Tool` 是工具的基本定义，描述工具的名称、描述和参数模式。

### 类定义

```python
class Tool(BaseModel):
    """可被模型识别的工具定义"""

    name: str
    """工具的名称"""

    description: str
    """工具的描述"""

    parameters: ParametersType
    """工具的参数，使用 JSON Schema 格式"""
```

### 使用示例

#### 示例 1：创建简单工具定义

```python
from kosong.tooling import Tool

# 定义一个获取天气的工具
weather_tool = Tool(
    name="get_weather",
    description="获取指定城市的天气信息",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "温度单位",
                "default": "celsius"
            }
        },
        "required": ["city"]
    }
)

print(weather_tool.name)  # "get_weather"
print(weather_tool.parameters["properties"]["city"])
# {'type': 'string', 'description': '城市名称'}
```

#### 示例 2：创建无参数工具

```python
from kosong.tooling import Tool

# 定义一个获取当前时间的工具
time_tool = Tool(
    name="get_current_time",
    description="获取当前时间",
    parameters={
        "type": "object",
        "properties": {}
    }
)
```

#### 示例 3：创建数组参数工具

```python
from kosong.tooling import Tool

# 定义一个计算数组和的工具
sum_tool = Tool(
    name="sum_numbers",
    description="计算数字数组的总和",
    parameters={
        "type": "array",
        "items": {
            "type": "number"
        },
        "description": "要求和的数字数组"
    }
)
```

### 参数验证

`Tool` 会自动验证 `parameters` 是否符合 JSON Schema 规范：

```python
from kosong.tooling import Tool
from pydantic import ValidationError

try:
    # 无效的 JSON Schema
    invalid_tool = Tool(
        name="invalid",
        description="Invalid tool",
        parameters={
            "type": "invalid_type"  # 无效的类型
        }
    )
except ValidationError as e:
    print("参数验证失败")
```


## ToolOk 类

`ToolOk` 表示工具成功执行后返回的结果。

### 类定义

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class ToolOk:
    """工具返回的成功输出"""

    output: str | ContentPart | Sequence[ContentPart]
    """工具返回的输出内容"""
    
    message: str = ""
    """给模型的解释性消息"""
    
    brief: str = ""
    """显示给用户的简短消息"""
```

### 使用示例

#### 示例 1：返回简单文本结果

```python
from kosong.tooling import ToolOk

# 返回简单的文本结果
result = ToolOk(
    output="北京：晴天，温度 25°C",
    message="成功获取天气信息",
    brief="天气查询成功"
)

print(result.output)  # "北京：晴天，温度 25°C"
print(result.message)  # "成功获取天气信息"
print(result.brief)  # "天气查询成功"
```

#### 示例 2：返回结构化内容

```python
from kosong.tooling import ToolOk
from kosong.message import TextPart, ImageURLPart

# 返回包含文本和图像的结果
result = ToolOk(
    output=[
        TextPart(text="这是查询到的图片："),
        ImageURLPart(
            image_url=ImageURLPart.ImageURL(
                url="https://example.com/weather-map.png"
            )
        )
    ],
    message="成功获取天气地图",
    brief="天气地图"
)
```

#### 示例 3：最小化返回

```python
from kosong.tooling import ToolOk

# 只返回必需的 output
result = ToolOk(output="42")
print(result.message)  # ""
print(result.brief)  # ""
```


## ToolError 类

`ToolError` 表示工具执行失败时返回的错误信息。注意这不是异常，而是正常的返回值。

### 类定义

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class ToolError:
    """工具返回的错误。这不是异常。"""

    output: str | ContentPart | Sequence[ContentPart] = ""
    """工具返回的输出内容"""
    
    message: str
    """给模型的错误消息"""
    
    brief: str
    """显示给用户的简短消息"""
```

### 使用示例

#### 示例 1：返回错误信息

```python
from kosong.tooling import ToolError

# 返回错误结果
error = ToolError(
    message="无法连接到天气服务 API",
    brief="天气查询失败"
)

print(error.message)  # "无法连接到天气服务 API"
print(error.brief)  # "天气查询失败"
print(error.output)  # ""
```

#### 示例 2：带输出内容的错误

```python
from kosong.tooling import ToolError

# 返回带部分信息的错误
error = ToolError(
    output="已查询到部分数据，但完整信息不可用",
    message="API 返回了不完整的数据",
    brief="数据不完整"
)
```

### 内置错误类型

`kosong.tooling.error` 模块提供了几个预定义的错误类型：

```python
from kosong.tooling.error import (
    ToolNotFoundError,
    ToolParseError,
    ToolValidateError,
    ToolRuntimeError,
)

# 工具未找到
error1 = ToolNotFoundError("get_weather")
# message: "Tool `get_weather` not found"
# brief: "Tool `get_weather` not found"

# JSON 解析错误
error2 = ToolParseError("Invalid JSON syntax")
# message: "Error parsing JSON arguments: Invalid JSON syntax"
# brief: "Invalid arguments"

# 参数验证错误
error3 = ToolValidateError("Missing required field: city")
# message: "Error validating JSON arguments: Missing required field: city"
# brief: "Invalid arguments"

# 运行时错误
error4 = ToolRuntimeError("Connection timeout")
# message: "Error running tool: Connection timeout"
# brief: "Tool runtime error"
```



## CallableTool 类

`CallableTool` 是可调用工具的抽象基类，允许你创建可以被实际执行的工具。

### 类定义

```python
class CallableTool(Tool, ABC):
    """
    可作为可调用对象调用的工具抽象基类。
    
    工具将使用 ToolCall 中提供的参数进行调用。
    - 如果参数是 JSON 数组，将解包为位置参数
    - 如果参数是 JSON 对象，将解包为关键字参数
    - 否则，参数将作为单个参数传递
    """

    @property
    def base(self) -> Tool:
        """基础工具定义"""
        return self

    async def call(self, arguments: JsonType) -> ToolReturnType:
        """调用工具并处理参数验证"""
        ...

    @abstractmethod
    async def __call__(self, *args: Any, **kwargs: Any) -> ToolReturnType:
        """工具的实现"""
        ...
```

### 使用示例

#### 示例 1：创建简单的计算工具

```python
from typing import override
from kosong.tooling import CallableTool, ToolOk, ToolError, ToolReturnType

class AddTool(CallableTool):
    name: str = "add"
    description: str = "将两个数字相加"
    parameters: dict = {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "第一个数字"},
            "b": {"type": "number", "description": "第二个数字"}
        },
        "required": ["a", "b"]
    }

    @override
    async def __call__(self, a: float, b: float) -> ToolReturnType:
        result = a + b
        return ToolOk(
            output=str(result),
            message=f"计算结果：{a} + {b} = {result}",
            brief=f"结果：{result}"
        )

# 使用工具
import asyncio

tool = AddTool()
result = asyncio.run(tool.call({"a": 10, "b": 20}))
print(result.output)  # "30"
```

#### 示例 2：创建带错误处理的工具

```python
from typing import override
from kosong.tooling import CallableTool, ToolOk, ToolError, ToolReturnType

class DivideTool(CallableTool):
    name: str = "divide"
    description: str = "将两个数字相除"
    parameters: dict = {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "被除数"},
            "b": {"type": "number", "description": "除数"}
        },
        "required": ["a", "b"]
    }

    @override
    async def __call__(self, a: float, b: float) -> ToolReturnType:
        if b == 0:
            return ToolError(
                message="除数不能为零",
                brief="除零错误"
            )
        
        result = a / b
        return ToolOk(
            output=str(result),
            message=f"{a} ÷ {b} = {result}",
            brief=f"结果：{result}"
        )

# 测试正常情况
tool = DivideTool()
result = asyncio.run(tool.call({"a": 10, "b": 2}))
print(result.output)  # "5.0"

# 测试错误情况
result = asyncio.run(tool.call({"a": 10, "b": 0}))
print(isinstance(result, ToolError))  # True
print(result.message)  # "除数不能为零"
```

#### 示例 3：使用数组参数

```python
from typing import override
from kosong.tooling import CallableTool, ToolOk, ToolReturnType

class SumTool(CallableTool):
    name: str = "sum"
    description: str = "计算数字列表的总和"
    parameters: dict = {
        "type": "array",
        "items": {"type": "number"}
    }

    @override
    async def __call__(self, *numbers: float) -> ToolReturnType:
        total = sum(numbers)
        return ToolOk(
            output=str(total),
            message=f"总和：{total}",
            brief=f"总和：{total}"
        )

# 使用数组参数
tool = SumTool()
result = asyncio.run(tool.call([1, 2, 3, 4, 5]))
print(result.output)  # "15"
```

#### 示例 4：创建异步 I/O 工具

```python
from typing import override
import aiohttp
from kosong.tooling import CallableTool, ToolOk, ToolError, ToolReturnType

class FetchURLTool(CallableTool):
    name: str = "fetch_url"
    description: str = "获取 URL 的内容"
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "要获取的 URL"}
        },
        "required": ["url"]
    }

    @override
    async def __call__(self, url: str) -> ToolReturnType:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()
                    return ToolOk(
                        output=content[:500],  # 只返回前 500 字符
                        message=f"成功获取 {url}",
                        brief="获取成功"
                    )
        except Exception as e:
            return ToolError(
                message=f"获取 URL 失败：{str(e)}",
                brief="获取失败"
            )
```

### 参数处理机制

`CallableTool` 会根据参数类型自动处理：

```python
# JSON 对象 -> 关键字参数
await tool.call({"a": 1, "b": 2})
# 等同于: await tool.__call__(a=1, b=2)

# JSON 数组 -> 位置参数
await tool.call([1, 2])
# 等同于: await tool.__call__(1, 2)

# 其他类型 -> 单个参数
await tool.call(42)
# 等同于: await tool.__call__(42)
```

### 自动参数验证

`CallableTool.call()` 会自动验证参数是否符合 JSON Schema：

```python
tool = AddTool()

# 有效参数
result = await tool.call({"a": 1, "b": 2})
# 返回 ToolOk

# 缺少必需参数
result = await tool.call({"a": 1})
# 返回 ToolValidateError

# 类型错误
result = await tool.call({"a": "not a number", "b": 2})
# 返回 ToolValidateError
```


## CallableTool2 类

`CallableTool2` 是带类型化参数的可调用工具抽象基类，使用 Pydantic 模型定义参数。

### 类定义

```python
class CallableTool2[Params: BaseModel](BaseModel, ABC):
    """
    带类型化参数的可调用工具抽象基类。
    
    工具将使用 ToolCall 中提供的参数进行调用。
    参数必须是 JSON 对象，并将通过 Pydantic 验证为 Params 类型。
    """

    name: str
    """工具的名称"""
    
    description: str
    """工具的描述"""
    
    params: type[Params]
    """工具参数的 Pydantic 模型类型"""

    @property
    def base(self) -> Tool:
        """基础工具定义"""
        return self._base

    async def call(self, arguments: JsonType) -> ToolReturnType:
        """调用工具并处理参数验证"""
        ...

    @abstractmethod
    async def __call__(self, params: Params) -> ToolReturnType:
        """工具的实现"""
        ...
```

### 使用示例

#### 示例 1：创建类型安全的工具

```python
from typing import override
from pydantic import BaseModel, Field
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType

class WeatherParams(BaseModel):
    city: str = Field(description="城市名称")
    unit: str = Field(
        default="celsius",
        description="温度单位",
        pattern="^(celsius|fahrenheit)$"
    )

class WeatherTool(CallableTool2[WeatherParams]):
    name: str = "get_weather"
    description: str = "获取指定城市的天气信息"
    params: type[WeatherParams] = WeatherParams

    @override
    async def __call__(self, params: WeatherParams) -> ToolReturnType:
        # params 是类型安全的 WeatherParams 对象
        weather_data = f"{params.city}：晴天，25°C"
        if params.unit == "fahrenheit":
            weather_data = f"{params.city}：晴天，77°F"
        
        return ToolOk(
            output=weather_data,
            message=f"成功获取 {params.city} 的天气",
            brief="天气查询成功"
        )

# 使用工具
import asyncio

tool = WeatherTool()
result = asyncio.run(tool.call({"city": "北京", "unit": "celsius"}))
print(result.output)  # "北京：晴天，25°C"

# 查看自动生成的 JSON Schema
print(tool.base.parameters)
# {
#     'type': 'object',
#     'properties': {
#         'city': {'type': 'string', 'description': '城市名称'},
#         'unit': {
#             'type': 'string',
#             'description': '温度单位',
#             'default': 'celsius',
#             'pattern': '^(celsius|fahrenheit)$'
#         }
#     },
#     'required': ['city']
# }
```

#### 示例 2：使用字段别名

```python
from typing import override
from pydantic import BaseModel, Field
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType

class SearchParams(BaseModel):
    query: str = Field(description="搜索查询")
    max_results: int = Field(
        default=10,
        alias="max-results",  # 使用连字符的别名
        description="最大结果数",
        ge=1,
        le=100
    )

class SearchTool(CallableTool2[SearchParams]):
    name: str = "search"
    description: str = "搜索信息"
    params: type[SearchParams] = SearchParams

    @override
    async def __call__(self, params: SearchParams) -> ToolReturnType:
        return ToolOk(
            output=f"找到 {params.max_results} 条关于 '{params.query}' 的结果",
            brief="搜索完成"
        )

# 使用别名
tool = SearchTool()
result = asyncio.run(tool.call({
    "query": "Python",
    "max-results": 20  # 使用别名
}))
print(result.output)  # "找到 20 条关于 'Python' 的结果"
```

#### 示例 3：复杂嵌套参数

```python
from typing import override
from pydantic import BaseModel, Field
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType

class Location(BaseModel):
    latitude: float = Field(description="纬度")
    longitude: float = Field(description="经度")

class MapParams(BaseModel):
    location: Location = Field(description="地图中心位置")
    zoom: int = Field(default=10, description="缩放级别", ge=1, le=20)
    map_type: str = Field(
        default="roadmap",
        description="地图类型",
        pattern="^(roadmap|satellite|hybrid)$"
    )

class MapTool(CallableTool2[MapParams]):
    name: str = "get_map"
    description: str = "获取地图图像"
    params: type[MapParams] = MapParams

    @override
    async def __call__(self, params: MapParams) -> ToolReturnType:
        return ToolOk(
            output=f"地图：{params.location.latitude},{params.location.longitude}",
            message=f"缩放级别 {params.zoom}，类型 {params.map_type}",
            brief="地图生成成功"
        )

# 使用嵌套参数
tool = MapTool()
result = asyncio.run(tool.call({
    "location": {"latitude": 39.9042, "longitude": 116.4074},
    "zoom": 15,
    "map_type": "satellite"
}))
```

### CallableTool vs CallableTool2

选择使用哪个基类：

| 特性 | CallableTool | CallableTool2 |
|------|-------------|---------------|
| 参数定义 | 手动编写 JSON Schema | 使用 Pydantic 模型 |
| 类型安全 | 否 | 是 |
| 参数验证 | JSON Schema 验证 | Pydantic 验证 |
| IDE 支持 | 有限 | 完整的类型提示 |
| 复杂度 | 简单 | 稍复杂 |
| 适用场景 | 简单工具 | 复杂参数结构 |

```python
# CallableTool：适合简单工具
class SimpleTool(CallableTool):
    parameters = {"type": "object", "properties": {"x": {"type": "number"}}}
    async def __call__(self, x: float) -> ToolReturnType:
        ...

# CallableTool2：适合复杂工具
class ComplexParams(BaseModel):
    x: float
    y: float
    options: dict[str, Any]

class ComplexTool(CallableTool2[ComplexParams]):
    params = ComplexParams
    async def __call__(self, params: ComplexParams) -> ToolReturnType:
        ...
```



## Toolset 协议

`Toolset` 是工具集的接口协议，定义了注册工具和处理工具调用的标准方法。

### 协议定义

```python
@runtime_checkable
class Toolset(Protocol):
    """可以注册工具并处理工具调用的工具集接口"""

    @property
    def tools(self) -> list[Tool]:
        """在此工具集中注册的工具定义列表"""
        ...

    def handle(self, tool_call: ToolCall) -> HandleResult:
        """
        处理工具调用。
        应返回工具调用的结果，或结果的异步 future。
        结果应该是 ToolReturnType，即 ToolOk 或 ToolError。

        此方法不得执行任何阻塞操作，因为它将在消费聊天响应流期间被调用。
        此方法不得引发任何异常，除了 asyncio.CancelledError。
        任何其他错误都应作为 ToolError 返回。
        """
        ...
```

### 类型定义

```python
from asyncio import Future
from kosong.tooling import ToolResult

# 工具结果
@dataclass(frozen=True)
class ToolResult:
    """工具调用的结果"""
    
    tool_call_id: str
    """工具调用的 ID"""
    
    result: ToolReturnType
    """工具调用的实际返回值"""

# 处理结果类型
ToolResultFuture = Future[ToolResult]
type HandleResult = ToolResultFuture | ToolResult
```

### 实现自定义 Toolset

```python
from kosong.message import ToolCall
from kosong.tooling import Toolset, Tool, HandleResult, ToolResult, ToolOk, ToolError
from kosong.tooling.error import ToolNotFoundError
import asyncio

class CustomToolset:
    """自定义工具集实现"""
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    @property
    def tools(self) -> list[Tool]:
        return list(self._tools.values())
    
    def add_tool(self, tool: Tool):
        """添加工具到工具集"""
        self._tools[tool.name] = tool
    
    def handle(self, tool_call: ToolCall) -> HandleResult:
        """处理工具调用"""
        tool_name = tool_call.function.name
        
        # 检查工具是否存在
        if tool_name not in self._tools:
            return ToolResult(
                tool_call_id=tool_call.id,
                result=ToolNotFoundError(tool_name)
            )
        
        # 创建异步任务处理工具调用
        async def _execute():
            try:
                # 这里实现实际的工具调用逻辑
                result = ToolOk(output="执行成功")
                return ToolResult(
                    tool_call_id=tool_call.id,
                    result=result
                )
            except Exception as e:
                return ToolResult(
                    tool_call_id=tool_call.id,
                    result=ToolError(
                        message=f"工具执行失败：{str(e)}",
                        brief="执行失败"
                    )
                )
        
        return asyncio.create_task(_execute())

# 验证实现符合协议
def type_check(toolset: CustomToolset):
    _: Toolset = toolset  # 类型检查通过
```


## SimpleToolset 类

`SimpleToolset` 是一个简单的工具集实现，可以并发处理工具调用。

### 类定义

```python
class SimpleToolset(Toolset):
    """可以并发处理工具调用的简单工具集"""

    def __init__(self, tools: Iterable[ToolType] | None = None):
        """使用可选的工具可迭代对象初始化简单工具集"""
        ...

    def __iadd__(self, tool: ToolType) -> Self:
        """添加工具到工具集"""
        ...

    def __add__(self, tool: ToolType) -> "SimpleToolset":
        """返回添加了给定工具的新工具集"""
        ...

    @property
    def tools(self) -> list[Tool]:
        """工具定义列表"""
        ...

    def handle(self, tool_call: ToolCall) -> HandleResult:
        """处理工具调用"""
        ...
```

### 使用示例

#### 示例 1：创建和使用工具集

```python
from kosong.tooling import CallableTool, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset
from typing import override
import asyncio

class AddTool(CallableTool):
    name: str = "add"
    description: str = "两数相加"
    parameters: dict = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        "required": ["a", "b"]
    }

    @override
    async def __call__(self, a: float, b: float) -> ToolReturnType:
        return ToolOk(output=str(a + b))

class MultiplyTool(CallableTool):
    name: str = "multiply"
    description: str = "两数相乘"
    parameters: dict = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"}
        },
        "required": ["a", "b"]
    }

    @override
    async def __call__(self, a: float, b: float) -> ToolReturnType:
        return ToolOk(output=str(a * b))

# 创建工具集
toolset = SimpleToolset([AddTool(), MultiplyTool()])

# 查看注册的工具
print([tool.name for tool in toolset.tools])
# ['add', 'multiply']
```

#### 示例 2：使用 += 运算符添加工具

```python
from kosong.tooling.simple import SimpleToolset

# 创建空工具集
toolset = SimpleToolset()

# 逐个添加工具
toolset += AddTool()
toolset += MultiplyTool()

print(len(toolset.tools))  # 2
```

#### 示例 3：使用 + 运算符创建新工具集

```python
from kosong.tooling.simple import SimpleToolset

# 创建基础工具集
base_toolset = SimpleToolset([AddTool()])

# 创建扩展的工具集（不修改原工具集）
extended_toolset = base_toolset + MultiplyTool()

print(len(base_toolset.tools))  # 1
print(len(extended_toolset.tools))  # 2
```

#### 示例 4：处理工具调用

```python
from kosong.message import ToolCall
from kosong.tooling import ToolResult
import asyncio

# 创建工具集
toolset = SimpleToolset([AddTool(), MultiplyTool()])

# 创建工具调用
tool_call = ToolCall(
    id="call_123",
    function=ToolCall.FunctionBody(
        name="add",
        arguments='{"a": 10, "b": 20}'
    )
)

# 处理工具调用
async def process():
    result = toolset.handle(tool_call)
    
    # result 可能是 ToolResult 或 Future[ToolResult]
    if isinstance(result, ToolResult):
        return result
    else:
        # 等待异步结果
        return await result

result = asyncio.run(process())
print(result.tool_call_id)  # "call_123"
print(result.result.output)  # "30"
```

#### 示例 5：并发处理多个工具调用

```python
from kosong.message import ToolCall
from kosong.tooling.simple import SimpleToolset
import asyncio

toolset = SimpleToolset([AddTool(), MultiplyTool()])

# 创建多个工具调用
tool_calls = [
    ToolCall(
        id="call_1",
        function=ToolCall.FunctionBody(name="add", arguments='{"a": 1, "b": 2}')
    ),
    ToolCall(
        id="call_2",
        function=ToolCall.FunctionBody(name="multiply", arguments='{"a": 3, "b": 4}')
    ),
    ToolCall(
        id="call_3",
        function=ToolCall.FunctionBody(name="add", arguments='{"a": 5, "b": 6}')
    ),
]

# 并发处理所有工具调用
async def process_all():
    futures = []
    for tool_call in tool_calls:
        result = toolset.handle(tool_call)
        if isinstance(result, asyncio.Future):
            futures.append(result)
        else:
            # 将同步结果包装为 future
            future = asyncio.Future()
            future.set_result(result)
            futures.append(future)
    
    # 等待所有结果
    return await asyncio.gather(*futures)

results = asyncio.run(process_all())
for result in results:
    print(f"{result.tool_call_id}: {result.result.output}")
# call_1: 3
# call_2: 12
# call_3: 11
```

#### 示例 6：错误处理

```python
from kosong.message import ToolCall
from kosong.tooling import ToolError
from kosong.tooling.error import ToolNotFoundError, ToolParseError, ToolValidateError
from kosong.tooling.simple import SimpleToolset
import asyncio

toolset = SimpleToolset([AddTool()])

# 测试各种错误情况
async def test_errors():
    # 1. 工具未找到
    call1 = ToolCall(
        id="call_1",
        function=ToolCall.FunctionBody(name="unknown", arguments="{}")
    )
    result1 = await toolset.handle(call1)
    assert isinstance(result1.result, ToolNotFoundError)
    print(result1.result.message)  # "Tool `unknown` not found"
    
    # 2. JSON 解析错误
    call2 = ToolCall(
        id="call_2",
        function=ToolCall.FunctionBody(name="add", arguments='invalid json')
    )
    result2 = await toolset.handle(call2)
    assert isinstance(result2.result, ToolParseError)
    print(result2.result.brief)  # "Invalid arguments"
    
    # 3. 参数验证错误
    call3 = ToolCall(
        id="call_3",
        function=ToolCall.FunctionBody(name="add", arguments='{"a": 1}')  # 缺少 b
    )
    result3 = await toolset.handle(call3)
    assert isinstance(result3.result, ToolValidateError)
    print(result3.result.brief)  # "Invalid arguments"

asyncio.run(test_errors())
```

#### 示例 7：在 generate 中使用

```python
from kosong import generate
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling.simple import SimpleToolset

# 创建工具集
toolset = SimpleToolset([AddTool(), MultiplyTool()])

# 在 generate 中使用
async def chat_with_tools():
    kimi = Kimi(api_key="your-api-key")
    
    result = await generate(
        chat_provider=kimi,
        system_prompt="你是一个数学助手。",
        tools=toolset.tools,  # 传递工具定义
        history=[
            Message(role="user", content="计算 15 + 27")
        ],
    )
    
    # 如果模型请求工具调用，处理它们
    if result.message.tool_calls:
        for tool_call in result.message.tool_calls:
            tool_result = await toolset.handle(tool_call)
            print(f"工具 {tool_call.function.name} 返回: {tool_result.result.output}")

# 运行
import asyncio
asyncio.run(chat_with_tools())
```

### 工具返回类型验证

`SimpleToolset` 会验证添加的工具是否返回正确的类型：

```python
from kosong.tooling import CallableTool, ToolReturnType
from kosong.tooling.simple import SimpleToolset
from typing import override

class InvalidTool(CallableTool):
    name: str = "invalid"
    description: str = "Invalid tool"
    parameters: dict = {"type": "object", "properties": {}}

    @override
    async def __call__(self) -> str:  # 错误的返回类型！
        return "invalid"

toolset = SimpleToolset()

try:
    toolset += InvalidTool()
except TypeError as e:
    print(e)
    # Expected tool `invalid` to return `ToolReturnType`, but got `<class 'str'>`
```

