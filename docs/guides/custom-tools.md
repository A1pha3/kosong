---
title: 自定义工具指南
description: 学习如何使用 Kosong 创建和使用自定义工具，扩展 AI Agent 的能力
version: 0.23.0
last_updated: 2025-01-15
---

# 自定义工具指南

自定义工具是 Kosong 框架的核心功能之一，它允许 AI Agent 调用外部函数来执行特定任务。通过创建自定义工具，你可以让 AI 访问数据库、调用 API、执行计算、操作文件系统等，极大地扩展 AI 的能力。

## 场景说明

自定义工具适用于以下场景：

- **数据查询**：让 AI 查询数据库、搜索文档、获取实时信息
- **外部 API 调用**：集成第三方服务（天气、地图、支付等）
- **计算任务**：执行复杂计算、数据处理、统计分析
- **文件操作**：读写文件、生成报告、处理图片
- **系统交互**：执行命令、管理资源、监控状态

## 工具的基本概念

在 Kosong 中，工具由三个核心部分组成：

1. **工具定义**（`Tool`）：描述工具的名称、功能和参数
2. **工具实现**（`CallableTool` 或 `CallableTool2`）：实际执行工具逻辑的代码
3. **工具集**（`Toolset`）：管理多个工具并处理工具调用

### 工具返回类型

工具执行后必须返回以下两种类型之一：

- **`ToolOk`**：表示工具成功执行，包含输出结果
- **`ToolError`**：表示工具执行失败，包含错误信息

```python
from kosong.tooling import ToolOk, ToolError

# 成功返回
return ToolOk(
    output="查询结果：北京今天晴天，温度 22°C",
    message="成功获取天气信息",  # 可选，给 AI 的说明
    brief="查询成功"  # 可选，给用户的简短说明
)

# 错误返回
return ToolError(
    message="无法连接到天气 API",  # 给 AI 的错误信息
    brief="查询失败",  # 给用户的简短说明
    output=""  # 可选，额外的错误详情
)
```

## 使用 CallableTool2 创建简单工具

`CallableTool2` 是推荐的工具创建方式，它使用 Pydantic 进行参数验证，类型安全且易于使用。

### 基础示例：计算器工具


```python
import asyncio

from pydantic import BaseModel, Field

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 1. 定义工具参数
class CalculatorParams(BaseModel):
    """计算器工具的参数定义。"""
    expression: str = Field(description="要计算的数学表达式，例如：'2 + 3 * 4'")


# 2. 创建工具类
class CalculatorTool(CallableTool2[CalculatorParams]):
    """一个简单的计算器工具。"""
    
    name: str = "calculator"
    description: str = "计算数学表达式的结果。支持基本的算术运算。"
    params: type[CalculatorParams] = CalculatorParams

    async def __call__(self, params: CalculatorParams) -> ToolReturnType:
        """执行计算。"""
        try:
            # 注意：在生产环境中应该使用更安全的表达式求值方法
            result = eval(params.expression)
            return ToolOk(
                output=f"计算结果：{result}",
                brief="计算成功"
            )
        except Exception as e:
            return ToolOk(
                output=f"计算错误：{str(e)}",
                brief="计算失败"
            )


# 3. 使用工具
async def main() -> None:
    # 初始化 ChatProvider
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    # 创建工具集并添加工具
    toolset = SimpleToolset()
    toolset += CalculatorTool()

    # 准备对话
    history = [
        Message(role="user", content="帮我算一下 123 * 456 等于多少？"),
    ]

    # 使用 step 自动执行工具
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个数学助手，可以使用计算器工具帮助用户进行计算。",
        toolset=toolset,
        history=history,
    )

    # 获取工具执行结果
    tool_results = await result.tool_results()
    
    # 显示结果
    print(f"AI 响应: {result.message.content}")
    for tr in tool_results:
        print(f"工具执行结果: {tr.result.output}")


asyncio.run(main())
```

**运行说明**：

1. 将 `your_kimi_api_key_here` 替换为你的 API 密钥
2. 运行脚本：`python calculator_tool.py`
3. AI 会自动调用计算器工具并返回结果

**预期输出**：

```
AI 响应: 让我帮你计算一下。
工具执行结果: 计算结果：56088
```

### 关键要点

- **参数定义**：使用 Pydantic `BaseModel` 定义参数，支持类型验证和描述
- **工具类**：继承 `CallableTool2[ParamsType]`，指定参数类型
- **必需属性**：`name`（工具名称）、`description`（工具描述）、`params`（参数类型）
- **实现方法**：`async def __call__(self, params: ParamsType) -> ToolReturnType`
- **返回类型**：必须返回 `ToolOk` 或 `ToolError`

## 工具参数验证

Pydantic 提供了强大的参数验证功能，确保工具接收到正确的输入。

### 参数类型和约束

```python
from pydantic import BaseModel, Field

class WeatherParams(BaseModel):
    """天气查询工具的参数。"""
    
    # 必需参数
    city: str = Field(description="要查询的城市名称")
    
    # 可选参数（带默认值）
    unit: str = Field(
        default="celsius",
        description="温度单位，可选值：celsius（摄氏度）或 fahrenheit（华氏度）"
    )
    
    # 带约束的参数
    days: int = Field(
        default=1,
        ge=1,  # 大于等于 1
        le=7,  # 小于等于 7
        description="预报天数，范围 1-7 天"
    )
    
    # 使用别名
    include_details: bool = Field(
        default=False,
        alias="details",
        description="是否包含详细信息"
    )
```

### 参数验证示例

```python
from pydantic import BaseModel, Field, field_validator

class SearchParams(BaseModel):
    """搜索工具的参数。"""
    
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=10, ge=1, le=100, description="最大结果数量")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """验证搜索关键词。"""
        if not v.strip():
            raise ValueError("搜索关键词不能为空")
        if len(v) > 200:
            raise ValueError("搜索关键词过长（最多 200 字符）")
        return v.strip()


class SearchTool(CallableTool2[SearchParams]):
    name: str = "search"
    description: str = "在知识库中搜索信息。"
    params: type[SearchParams] = SearchParams

    async def __call__(self, params: SearchParams) -> ToolReturnType:
        # 参数已经通过验证，可以安全使用
        results = await self._search(params.query, params.max_results)
        return ToolOk(output=f"找到 {len(results)} 条结果")
    
    async def _search(self, query: str, max_results: int) -> list[str]:
        # 实际的搜索逻辑
        return []
```

**验证失败时的行为**：

- Kosong 会自动捕获 Pydantic 验证错误
- 返回 `ToolValidateError` 给 AI
- AI 会收到错误信息并可能重试或告知用户

## 工具错误处理

正确的错误处理能让 AI 更好地理解问题并采取适当的行动。

### 基础错误处理

```python
from pydantic import BaseModel, Field

import kosong
from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType


class FileReadParams(BaseModel):
    filepath: str = Field(description="要读取的文件路径")


class FileReadTool(CallableTool2[FileReadParams]):
    name: str = "read_file"
    description: str = "读取文件内容。"
    params: type[FileReadParams] = FileReadParams

    async def __call__(self, params: FileReadParams) -> ToolReturnType:
        try:
            # 尝试读取文件
            with open(params.filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            return ToolOk(
                output=content,
                message=f"成功读取文件 {params.filepath}",
                brief="读取成功"
            )
        
        except FileNotFoundError:
            # 文件不存在
            return ToolError(
                message=f"文件不存在：{params.filepath}",
                brief="文件未找到"
            )
        
        except PermissionError:
            # 权限不足
            return ToolError(
                message=f"没有权限读取文件：{params.filepath}",
                brief="权限不足"
            )
        
        except UnicodeDecodeError:
            # 编码错误
            return ToolError(
                message=f"文件编码错误，无法读取：{params.filepath}",
                brief="编码错误"
            )
        
        except Exception as e:
            # 其他未知错误
            return ToolError(
                message=f"读取文件时发生错误：{str(e)}",
                brief="读取失败"
            )
```

### 错误处理最佳实践

1. **区分不同类型的错误**：让 AI 了解具体的失败原因
2. **提供清晰的错误信息**：`message` 给 AI 详细说明，`brief` 给用户简短提示
3. **避免抛出异常**：在工具内部捕获所有异常并返回 `ToolError`
4. **记录日志**：对于重要错误，记录日志便于调试

```python
import logging

logger = logging.getLogger(__name__)


class RobustTool(CallableTool2[SomeParams]):
    name: str = "robust_tool"
    description: str = "一个健壮的工具示例。"
    params: type[SomeParams] = SomeParams

    async def __call__(self, params: SomeParams) -> ToolReturnType:
        try:
            result = await self._do_work(params)
            return ToolOk(output=result)
        
        except ValueError as e:
            # 预期的错误，不需要记录
            return ToolError(
                message=f"参数错误：{str(e)}",
                brief="参数无效"
            )
        
        except Exception as e:
            # 意外的错误，记录日志
            logger.error(f"工具执行失败: {e}", exc_info=True)
            return ToolError(
                message=f"工具执行失败：{str(e)}",
                brief="执行失败"
            )
    
    async def _do_work(self, params: SomeParams) -> str:
        # 实际的工作逻辑
        return "result"
```



## 异步工具实现

Kosong 的工具都是异步的，这允许你在工具中执行 I/O 操作而不阻塞其他任务。

### 异步 API 调用

```python
import asyncio

import httpx
from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType


class WeatherParams(BaseModel):
    city: str = Field(description="城市名称")


class WeatherTool(CallableTool2[WeatherParams]):
    """异步天气查询工具。"""
    
    name: str = "get_weather"
    description: str = "查询指定城市的实时天气信息。"
    params: type[WeatherParams] = WeatherParams

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 创建可复用的 HTTP 客户端
        self.client = httpx.AsyncClient(timeout=10.0)

    async def __call__(self, params: WeatherParams) -> ToolReturnType:
        try:
            # 异步 HTTP 请求
            response = await self.client.get(
                "https://api.weather.example.com/current",
                params={"city": params.city}
            )
            response.raise_for_status()
            
            data = response.json()
            weather_info = (
                f"{params.city}的天气：{data['condition']}，"
                f"温度 {data['temperature']}°C，"
                f"湿度 {data['humidity']}%"
            )
            
            return ToolOk(
                output=weather_info,
                brief="查询成功"
            )
        
        except httpx.TimeoutException:
            return ToolError(
                message=f"查询 {params.city} 天气超时",
                brief="请求超时"
            )
        
        except httpx.HTTPStatusError as e:
            return ToolError(
                message=f"天气 API 返回错误：{e.response.status_code}",
                brief="API 错误"
            )
        
        except Exception as e:
            return ToolError(
                message=f"查询天气失败：{str(e)}",
                brief="查询失败"
            )
    
    async def __del__(self):
        """清理资源。"""
        await self.client.aclose()
```

### 异步数据库操作

```python
import asyncio

from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType


class UserQueryParams(BaseModel):
    user_id: int = Field(description="用户 ID")


class UserQueryTool(CallableTool2[UserQueryParams]):
    """异步数据库查询工具。"""
    
    name: str = "query_user"
    description: str = "根据用户 ID 查询用户信息。"
    params: type[UserQueryParams] = UserQueryParams

    def __init__(self, db_pool, **kwargs):
        super().__init__(**kwargs)
        self.db_pool = db_pool  # 数据库连接池

    async def __call__(self, params: UserQueryParams) -> ToolReturnType:
        try:
            # 异步数据库查询
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT name, email, created_at FROM users WHERE id = $1",
                    params.user_id
                )
            
            if row is None:
                return ToolError(
                    message=f"未找到 ID 为 {params.user_id} 的用户",
                    brief="用户不存在"
                )
            
            user_info = (
                f"用户信息：\n"
                f"姓名：{row['name']}\n"
                f"邮箱：{row['email']}\n"
                f"注册时间：{row['created_at']}"
            )
            
            return ToolOk(
                output=user_info,
                brief="查询成功"
            )
        
        except Exception as e:
            return ToolError(
                message=f"数据库查询失败：{str(e)}",
                brief="查询失败"
            )
```

### 并发执行多个异步操作

```python
import asyncio

from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType


class MultiCityWeatherParams(BaseModel):
    cities: list[str] = Field(description="城市列表")


class MultiCityWeatherTool(CallableTool2[MultiCityWeatherParams]):
    """并发查询多个城市的天气。"""
    
    name: str = "get_multi_city_weather"
    description: str = "同时查询多个城市的天气信息。"
    params: type[MultiCityWeatherParams] = MultiCityWeatherParams

    async def __call__(self, params: MultiCityWeatherParams) -> ToolReturnType:
        try:
            # 并发查询所有城市
            tasks = [self._fetch_weather(city) for city in params.cities]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 整理结果
            weather_reports = []
            for city, result in zip(params.cities, results):
                if isinstance(result, Exception):
                    weather_reports.append(f"{city}：查询失败")
                else:
                    weather_reports.append(f"{city}：{result}")
            
            return ToolOk(
                output="\n".join(weather_reports),
                brief=f"查询了 {len(params.cities)} 个城市"
            )
        
        except Exception as e:
            return ToolError(
                message=f"批量查询失败：{str(e)}",
                brief="查询失败"
            )
    
    async def _fetch_weather(self, city: str) -> str:
        """查询单个城市的天气。"""
        # 模拟 API 调用
        await asyncio.sleep(0.5)
        return f"晴天，22°C"
```

**异步工具的优势**：

- 不阻塞其他工具的执行
- 可以并发处理多个请求
- 提高整体响应速度
- 更好地利用系统资源

## 工具组合和复用

### 创建工具基类

通过继承，可以在多个工具之间共享逻辑：

```python
from abc import ABC
from pydantic import BaseModel

import httpx
from kosong.tooling import CallableTool2, ToolError, ToolReturnType


class APIToolBase(CallableTool2[BaseModel], ABC):
    """API 工具的基类，提供通用的 HTTP 请求功能。"""
    
    def __init__(self, api_key: str, base_url: str, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
    
    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """通用的 GET 请求方法。"""
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"API 请求失败：{str(e)}")
    
    async def _post(self, endpoint: str, data: dict) -> dict:
        """通用的 POST 请求方法。"""
        try:
            response = await self.client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"API 请求失败：{str(e)}")


# 使用基类创建具体工具
class WeatherQueryParams(BaseModel):
    city: str


class WeatherQueryTool(APIToolBase):
    name: str = "weather_query"
    description: str = "查询天气信息。"
    params: type[WeatherQueryParams] = WeatherQueryParams

    async def __call__(self, params: WeatherQueryParams) -> ToolReturnType:
        try:
            data = await self._get("/weather", {"city": params.city})
            return ToolOk(output=f"{params.city}：{data['condition']}")
        except Exception as e:
            return ToolError(message=str(e), brief="查询失败")


class ForecastQueryParams(BaseModel):
    city: str
    days: int


class ForecastQueryTool(APIToolBase):
    name: str = "forecast_query"
    description: str = "查询天气预报。"
    params: type[ForecastQueryParams] = ForecastQueryParams

    async def __call__(self, params: ForecastQueryParams) -> ToolReturnType:
        try:
            data = await self._get(
                "/forecast",
                {"city": params.city, "days": params.days}
            )
            return ToolOk(output=f"{params.city} 未来 {params.days} 天预报")
        except Exception as e:
            return ToolError(message=str(e), brief="查询失败")
```

### 组合多个工具

```python
from kosong.tooling.simple import SimpleToolset


def create_weather_toolset(api_key: str) -> SimpleToolset:
    """创建包含所有天气相关工具的工具集。"""
    toolset = SimpleToolset()
    
    base_url = "https://api.weather.example.com"
    
    # 添加多个工具
    toolset += WeatherQueryTool(api_key=api_key, base_url=base_url)
    toolset += ForecastQueryTool(api_key=api_key, base_url=base_url)
    
    return toolset


# 使用
async def main():
    toolset = create_weather_toolset("your_api_key")
    
    result = await kosong.step(
        chat_provider=kimi,
        system_prompt="你是一个天气助手。",
        toolset=toolset,
        history=history,
    )
```

### 工具装饰器模式

创建可复用的工具增强功能：

```python
import time
import logging
from typing import Any

from kosong.tooling import CallableTool2, ToolReturnType

logger = logging.getLogger(__name__)


class LoggedTool(CallableTool2[Any]):
    """带日志记录的工具装饰器。"""
    
    def __init__(self, wrapped_tool: CallableTool2[Any], **kwargs):
        # 复制被包装工具的属性
        super().__init__(
            name=wrapped_tool.name,
            description=wrapped_tool.description,
            params=wrapped_tool.params,
            **kwargs
        )
        self.wrapped_tool = wrapped_tool
    
    async def __call__(self, params: Any) -> ToolReturnType:
        start_time = time.time()
        logger.info(f"开始执行工具: {self.name}")
        
        try:
            result = await self.wrapped_tool(params)
            elapsed = time.time() - start_time
            logger.info(f"工具执行成功: {self.name}, 耗时: {elapsed:.2f}s")
            return result
        
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"工具执行失败: {self.name}, 耗时: {elapsed:.2f}s, 错误: {e}")
            raise


# 使用装饰器
toolset = SimpleToolset()
toolset += LoggedTool(CalculatorTool())
toolset += LoggedTool(WeatherTool())
```



## 完整示例：文件管理工具集

下面是一个完整的示例，展示如何创建一组相关的工具：

```python
import asyncio
import os
from pathlib import Path

from pydantic import BaseModel, Field

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 1. 列出目录内容
class ListDirParams(BaseModel):
    path: str = Field(default=".", description="目录路径")


class ListDirTool(CallableTool2[ListDirParams]):
    name: str = "list_directory"
    description: str = "列出指定目录中的文件和子目录。"
    params: type[ListDirParams] = ListDirParams

    async def __call__(self, params: ListDirParams) -> ToolReturnType:
        try:
            path = Path(params.path)
            if not path.exists():
                return ToolError(
                    message=f"目录不存在：{params.path}",
                    brief="目录不存在"
                )
            
            if not path.is_dir():
                return ToolError(
                    message=f"路径不是目录：{params.path}",
                    brief="不是目录"
                )
            
            items = []
            for item in path.iterdir():
                item_type = "目录" if item.is_dir() else "文件"
                items.append(f"[{item_type}] {item.name}")
            
            if not items:
                output = f"目录 {params.path} 是空的"
            else:
                output = f"目录 {params.path} 的内容：\n" + "\n".join(items)
            
            return ToolOk(output=output, brief="列出成功")
        
        except PermissionError:
            return ToolError(
                message=f"没有权限访问目录：{params.path}",
                brief="权限不足"
            )
        except Exception as e:
            return ToolError(
                message=f"列出目录失败：{str(e)}",
                brief="操作失败"
            )


# 2. 读取文件
class ReadFileParams(BaseModel):
    filepath: str = Field(description="文件路径")
    max_lines: int = Field(default=100, description="最多读取的行数")


class ReadFileTool(CallableTool2[ReadFileParams]):
    name: str = "read_file"
    description: str = "读取文本文件的内容。"
    params: type[ReadFileParams] = ReadFileParams

    async def __call__(self, params: ReadFileParams) -> ToolReturnType:
        try:
            path = Path(params.filepath)
            if not path.exists():
                return ToolError(
                    message=f"文件不存在：{params.filepath}",
                    brief="文件不存在"
                )
            
            if not path.is_file():
                return ToolError(
                    message=f"路径不是文件：{params.filepath}",
                    brief="不是文件"
                )
            
            with open(path, "r", encoding="utf-8") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= params.max_lines:
                        lines.append(f"\n... (文件还有更多内容，已省略)")
                        break
                    lines.append(line.rstrip())
            
            content = "\n".join(lines)
            return ToolOk(
                output=f"文件 {params.filepath} 的内容：\n{content}",
                brief="读取成功"
            )
        
        except UnicodeDecodeError:
            return ToolError(
                message=f"文件不是文本文件或编码不支持：{params.filepath}",
                brief="编码错误"
            )
        except Exception as e:
            return ToolError(
                message=f"读取文件失败：{str(e)}",
                brief="读取失败"
            )


# 3. 写入文件
class WriteFileParams(BaseModel):
    filepath: str = Field(description="文件路径")
    content: str = Field(description="要写入的内容")
    append: bool = Field(default=False, description="是否追加到文件末尾")


class WriteFileTool(CallableTool2[WriteFileParams]):
    name: str = "write_file"
    description: str = "将内容写入文件。"
    params: type[WriteFileParams] = WriteFileParams

    async def __call__(self, params: WriteFileParams) -> ToolReturnType:
        try:
            path = Path(params.filepath)
            
            # 确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = "a" if params.append else "w"
            with open(path, mode, encoding="utf-8") as f:
                f.write(params.content)
            
            action = "追加" if params.append else "写入"
            return ToolOk(
                output=f"成功{action}内容到文件：{params.filepath}",
                brief=f"{action}成功"
            )
        
        except PermissionError:
            return ToolError(
                message=f"没有权限写入文件：{params.filepath}",
                brief="权限不足"
            )
        except Exception as e:
            return ToolError(
                message=f"写入文件失败：{str(e)}",
                brief="写入失败"
            )


# 4. 获取文件信息
class FileInfoParams(BaseModel):
    filepath: str = Field(description="文件或目录路径")


class FileInfoTool(CallableTool2[FileInfoParams]):
    name: str = "get_file_info"
    description: str = "获取文件或目录的详细信息。"
    params: type[FileInfoParams] = FileInfoParams

    async def __call__(self, params: FileInfoParams) -> ToolReturnType:
        try:
            path = Path(params.filepath)
            if not path.exists():
                return ToolError(
                    message=f"路径不存在：{params.filepath}",
                    brief="路径不存在"
                )
            
            stat = path.stat()
            item_type = "目录" if path.is_dir() else "文件"
            
            info = [
                f"路径：{params.filepath}",
                f"类型：{item_type}",
                f"大小：{stat.st_size} 字节",
                f"修改时间：{stat.st_mtime}",
            ]
            
            if path.is_file():
                info.append(f"是否可读：{'是' if os.access(path, os.R_OK) else '否'}")
                info.append(f"是否可写：{'是' if os.access(path, os.W_OK) else '否'}")
            
            return ToolOk(
                output="\n".join(info),
                brief="获取成功"
            )
        
        except Exception as e:
            return ToolError(
                message=f"获取文件信息失败：{str(e)}",
                brief="获取失败"
            )


# 5. 创建工具集
def create_file_toolset() -> SimpleToolset:
    """创建文件管理工具集。"""
    toolset = SimpleToolset()
    toolset += ListDirTool()
    toolset += ReadFileTool()
    toolset += WriteFileTool()
    toolset += FileInfoTool()
    return toolset


# 6. 使用示例
async def main() -> None:
    kimi = Kimi(
        base_url="https://api.moonshot.ai/v1",
        api_key="your_kimi_api_key_here",
        model="kimi-k2-turbo-preview",
    )

    toolset = create_file_toolset()

    system_prompt = """你是一个文件管理助手，可以帮助用户管理文件和目录。
你可以：
- 列出目录内容
- 读取文件
- 写入文件
- 获取文件信息

注意：在执行写入操作前，请先确认用户的意图。"""

    history = [
        Message(role="user", content="列出当前目录的内容"),
    ]

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
        
        # 显示 AI 响应
        if isinstance(result.message.content, str):
            print(f"AI: {result.message.content}")
        
        # 显示工具执行结果
        for tr in tool_results:
            print(f"[工具执行]: {tr.result.output}")

        # 如果没有工具调用，结束
        if not result.tool_calls:
            break

        # 将结果添加到历史
        history.append(result.message)
        from kosong.message import ContentPart, TextPart
        for tr in tool_results:
            match tr.result.output:
                case str():
                    content = tr.result.output
                case ContentPart() as part:
                    content = [part]
                case _:
                    content = list(tr.result.output)
            history.append(
                Message(role="tool", tool_call_id=tr.tool_call_id, content=content)
            )


asyncio.run(main())
```

**运行说明**：

1. 替换 API 密钥
2. 运行脚本：`python file_manager.py`
3. AI 会调用相应的文件管理工具

**示例对话**：

```
用户: 列出当前目录的内容
AI: 让我为你列出当前目录的内容。
[工具执行]: 目录 . 的内容：
[文件] main.py
[文件] README.md
[目录] src
[目录] tests

用户: 读取 README.md 文件
AI: 我来读取 README.md 文件的内容。
[工具执行]: 文件 README.md 的内容：
# 项目说明
这是一个示例项目...
```

## 高级技巧

### 1. 工具状态管理

有些工具需要维护状态（如数据库连接、缓存等）：

```python
from typing import Any

class StatefulTool(CallableTool2[SomeParams]):
    """带状态的工具示例。"""
    
    name: str = "stateful_tool"
    description: str = "一个带状态的工具。"
    params: type[SomeParams] = SomeParams

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache: dict[str, Any] = {}
        self.call_count = 0

    async def __call__(self, params: SomeParams) -> ToolReturnType:
        self.call_count += 1
        
        # 使用缓存
        cache_key = str(params)
        if cache_key in self.cache:
            return ToolOk(
                output=f"从缓存返回结果（第 {self.call_count} 次调用）",
                brief="缓存命中"
            )
        
        # 执行实际操作
        result = await self._do_work(params)
        self.cache[cache_key] = result
        
        return ToolOk(
            output=f"执行完成（第 {self.call_count} 次调用）",
            brief="执行成功"
        )
    
    async def _do_work(self, params: SomeParams) -> str:
        return "result"
```

### 2. 工具权限控制

为敏感操作添加权限检查：

```python
class SecureTool(CallableTool2[SomeParams]):
    """带权限控制的工具。"""
    
    name: str = "secure_tool"
    description: str = "一个需要权限的工具。"
    params: type[SomeParams] = SomeParams

    def __init__(self, allowed_users: set[str], **kwargs):
        super().__init__(**kwargs)
        self.allowed_users = allowed_users

    async def __call__(self, params: SomeParams) -> ToolReturnType:
        # 假设从上下文获取当前用户
        current_user = self._get_current_user()
        
        if current_user not in self.allowed_users:
            return ToolError(
                message=f"用户 {current_user} 没有权限使用此工具",
                brief="权限不足"
            )
        
        # 执行实际操作
        return await self._execute(params)
    
    def _get_current_user(self) -> str:
        # 从上下文获取用户信息
        return "user123"
    
    async def _execute(self, params: SomeParams) -> ToolReturnType:
        return ToolOk(output="执行成功")
```

### 3. 工具超时控制

为长时间运行的工具添加超时：

```python
import asyncio

class TimeoutTool(CallableTool2[SomeParams]):
    """带超时控制的工具。"""
    
    name: str = "timeout_tool"
    description: str = "一个带超时的工具。"
    params: type[SomeParams] = SomeParams

    def __init__(self, timeout: float = 30.0, **kwargs):
        super().__init__(**kwargs)
        self.timeout = timeout

    async def __call__(self, params: SomeParams) -> ToolReturnType:
        try:
            # 使用 asyncio.wait_for 添加超时
            result = await asyncio.wait_for(
                self._do_work(params),
                timeout=self.timeout
            )
            return ToolOk(output=result)
        
        except asyncio.TimeoutError:
            return ToolError(
                message=f"工具执行超时（超过 {self.timeout} 秒）",
                brief="执行超时"
            )
        except Exception as e:
            return ToolError(
                message=f"工具执行失败：{str(e)}",
                brief="执行失败"
            )
    
    async def _do_work(self, params: SomeParams) -> str:
        # 可能耗时的操作
        await asyncio.sleep(5)
        return "result"
```

### 4. 工具重试机制

为不稳定的操作添加重试：

```python
import asyncio

class RetryableTool(CallableTool2[SomeParams]):
    """带重试机制的工具。"""
    
    name: str = "retryable_tool"
    description: str = "一个带重试的工具。"
    params: type[SomeParams] = SomeParams

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def __call__(self, params: SomeParams) -> ToolReturnType:
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self._do_work(params)
                return ToolOk(output=result)
            
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # 等待后重试
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
        
        # 所有重试都失败
        return ToolError(
            message=f"工具执行失败（已重试 {self.max_retries} 次）：{str(last_error)}",
            brief="执行失败"
        )
    
    async def _do_work(self, params: SomeParams) -> str:
        # 可能失败的操作
        return "result"
```



## 使用 CallableTool（传统方式）

除了 `CallableTool2`，Kosong 还支持传统的 `CallableTool` 方式。这种方式使用 JSON Schema 定义参数，更加灵活但类型安全性较低。

### CallableTool 基础示例

```python
from typing import override

from kosong.tooling import CallableTool, ParametersType, ToolOk, ToolReturnType


class LegacyCalculatorTool(CallableTool):
    """使用 CallableTool 的计算器工具。"""
    
    name: str = "calculator"
    description: str = "计算数学表达式的结果。"
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式"
            }
        },
        "required": ["expression"]
    }

    @override
    async def __call__(self, expression: str) -> ToolReturnType:
        try:
            result = eval(expression)
            return ToolOk(output=f"计算结果：{result}")
        except Exception as e:
            return ToolOk(output=f"计算错误：{str(e)}")
```

### CallableTool 参数类型

`CallableTool` 支持三种参数传递方式：

```python
from typing import override

from kosong.tooling import CallableTool, ParametersType, ToolOk, ToolReturnType


# 1. 对象参数（字典）
class ObjectParamsTool(CallableTool):
    name: str = "object_tool"
    description: str = "接收对象参数的工具"
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "string"}
        },
        "required": ["a", "b"]
    }

    @override
    async def __call__(self, a: int, b: str) -> ToolReturnType:
        # 参数会被解包为关键字参数
        return ToolOk(output=f"a={a}, b={b}")


# 2. 数组参数（列表）
class ArrayParamsTool(CallableTool):
    name: str = "array_tool"
    description: str = "接收数组参数的工具"
    parameters: ParametersType = {
        "type": "array",
        "items": {"type": "string"}
    }

    @override
    async def __call__(self, *args: str) -> ToolReturnType:
        # 参数会被解包为位置参数
        return ToolOk(output=f"收到 {len(args)} 个参数")


# 3. 单一参数
class SingleParamTool(CallableTool):
    name: str = "single_tool"
    description: str = "接收单一参数的工具"
    parameters: ParametersType = {
        "type": "integer"
    }

    @override
    async def __call__(self, value: int) -> ToolReturnType:
        # 参数直接传递
        return ToolOk(output=f"值为 {value}")
```

### CallableTool vs CallableTool2

| 特性 | CallableTool | CallableTool2 |
|------|-------------|---------------|
| 参数定义 | JSON Schema | Pydantic BaseModel |
| 类型安全 | 较低 | 高 |
| 参数验证 | JSON Schema 验证 | Pydantic 验证 |
| IDE 支持 | 一般 | 优秀 |
| 灵活性 | 高 | 中 |
| 推荐使用 | 特殊场景 | 日常开发 |

**推荐**：优先使用 `CallableTool2`，除非你需要：
- 动态生成参数 schema
- 使用 JSON Schema 的高级特性
- 与现有 JSON Schema 集成

## 测试自定义工具

### 单元测试

```python
import asyncio
import pytest

from pydantic import BaseModel, Field

from kosong.tooling import CallableTool2, ToolOk, ToolError, ToolReturnType


class TestParams(BaseModel):
    value: int = Field(ge=0, le=100)


class TestTool(CallableTool2[TestParams]):
    name: str = "test_tool"
    description: str = "测试工具"
    params: type[TestParams] = TestParams

    async def __call__(self, params: TestParams) -> ToolReturnType:
        if params.value == 42:
            return ToolOk(output="正确答案！")
        return ToolError(message="错误答案", brief="错误")


# 测试用例
@pytest.mark.asyncio
async def test_tool_success():
    """测试工具成功执行。"""
    tool = TestTool()
    result = await tool.call({"value": 42})
    
    assert isinstance(result, ToolOk)
    assert result.output == "正确答案！"


@pytest.mark.asyncio
async def test_tool_error():
    """测试工具返回错误。"""
    tool = TestTool()
    result = await tool.call({"value": 10})
    
    assert isinstance(result, ToolError)
    assert result.message == "错误答案"


@pytest.mark.asyncio
async def test_tool_validation():
    """测试参数验证。"""
    tool = TestTool()
    
    # 测试无效参数
    result = await tool.call({"value": 200})  # 超出范围
    assert isinstance(result, ToolError)
    
    # 测试缺失参数
    result = await tool.call({})
    assert isinstance(result, ToolError)
```

### 集成测试

```python
import asyncio
import pytest

from kosong.chat_provider.mock import Mock
from kosong.message import Message, ToolCall
from kosong.tooling.simple import SimpleToolset

import kosong


@pytest.mark.asyncio
async def test_tool_integration():
    """测试工具与 Kosong 的集成。"""
    # 创建 Mock Provider
    mock_provider = Mock(
        responses=[
            [
                ToolCall(
                    id="call_1",
                    function=ToolCall.FunctionBody(
                        name="test_tool",
                        arguments='{"value": 42}'
                    )
                )
            ]
        ]
    )
    
    # 创建工具集
    toolset = SimpleToolset()
    toolset += TestTool()
    
    # 执行
    result = await kosong.step(
        chat_provider=mock_provider,
        system_prompt="测试",
        toolset=toolset,
        history=[Message(role="user", content="测试")],
    )
    
    # 验证
    tool_results = await result.tool_results()
    assert len(tool_results) == 1
    assert isinstance(tool_results[0].result, ToolOk)
```

## 最佳实践

### 1. 工具设计原则

- **单一职责**：每个工具只做一件事
- **清晰命名**：工具名称应该准确描述其功能
- **详细描述**：帮助 AI 理解何时使用该工具
- **参数简洁**：避免过多或过于复杂的参数
- **幂等性**：相同输入应产生相同输出（如果可能）

```python
# 好的设计
class GetUserTool(CallableTool2[GetUserParams]):
    name: str = "get_user"  # 清晰的名称
    description: str = "根据用户 ID 获取用户的基本信息（姓名、邮箱、注册时间）。"  # 详细描述
    params: type[GetUserParams] = GetUserParams  # 简单参数

# 不好的设计
class UserTool(CallableTool2[ComplexParams]):
    name: str = "user"  # 名称不清晰
    description: str = "用户相关操作"  # 描述太模糊
    params: type[ComplexParams] = ComplexParams  # 参数过于复杂
```

### 2. 错误处理策略

- **捕获所有异常**：不要让异常传播到框架层
- **提供有用的错误信息**：帮助 AI 理解问题并采取行动
- **区分错误类型**：让 AI 知道是参数错误、权限错误还是系统错误
- **记录日志**：便于调试和监控

```python
async def __call__(self, params: SomeParams) -> ToolReturnType:
    try:
        # 参数验证
        if not self._validate_params(params):
            return ToolError(
                message="参数验证失败：...",
                brief="参数无效"
            )
        
        # 权限检查
        if not self._check_permission():
            return ToolError(
                message="当前用户没有权限执行此操作",
                brief="权限不足"
            )
        
        # 执行操作
        result = await self._execute(params)
        return ToolOk(output=result)
    
    except ValueError as e:
        # 预期的业务错误
        return ToolError(message=str(e), brief="操作失败")
    
    except Exception as e:
        # 意外错误，记录日志
        logger.error(f"工具执行失败: {e}", exc_info=True)
        return ToolError(
            message="系统错误，请稍后重试",
            brief="系统错误"
        )
```

### 3. 性能优化

- **使用连接池**：复用数据库连接、HTTP 客户端等
- **实现缓存**：缓存频繁访问的数据
- **并发执行**：使用 `asyncio.gather` 并发处理多个任务
- **设置超时**：避免长时间阻塞

```python
class OptimizedTool(CallableTool2[SomeParams]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 复用 HTTP 客户端
        self.client = httpx.AsyncClient()
        # 简单的内存缓存
        self.cache: dict[str, tuple[float, str]] = {}
        self.cache_ttl = 300  # 5 分钟

    async def __call__(self, params: SomeParams) -> ToolReturnType:
        # 检查缓存
        cache_key = str(params)
        if cache_key in self.cache:
            timestamp, result = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return ToolOk(output=result, brief="从缓存返回")
        
        # 执行操作
        result = await self._fetch_data(params)
        
        # 更新缓存
        self.cache[cache_key] = (time.time(), result)
        
        return ToolOk(output=result)
```

### 4. 安全考虑

- **输入验证**：严格验证所有输入参数
- **权限控制**：检查用户权限
- **避免注入攻击**：不要直接执行用户输入的代码或 SQL
- **限制资源使用**：防止滥用（如限制文件大小、请求频率）

```python
class SecureFileTool(CallableTool2[FileParams]):
    def __init__(self, allowed_dirs: list[str], **kwargs):
        super().__init__(**kwargs)
        self.allowed_dirs = [Path(d).resolve() for d in allowed_dirs]

    async def __call__(self, params: FileParams) -> ToolReturnType:
        # 解析路径
        filepath = Path(params.filepath).resolve()
        
        # 检查路径是否在允许的目录中
        if not any(
            str(filepath).startswith(str(allowed_dir))
            for allowed_dir in self.allowed_dirs
        ):
            return ToolError(
                message=f"不允许访问路径：{params.filepath}",
                brief="路径不允许"
            )
        
        # 检查文件大小
        if filepath.exists() and filepath.stat().st_size > 10 * 1024 * 1024:
            return ToolError(
                message="文件过大（超过 10MB）",
                brief="文件过大"
            )
        
        # 执行操作
        return await self._process_file(filepath)
```

## 常见问题

### Q: 何时使用 CallableTool2 vs CallableTool？

A: 推荐优先使用 `CallableTool2`：

- **使用 CallableTool2**：日常开发、需要类型安全、参数结构固定
- **使用 CallableTool**：需要动态生成 schema、使用 JSON Schema 高级特性

### Q: 工具可以调用其他工具吗？

A: 不建议。工具应该是独立的、原子的操作。如果需要组合多个操作，让 AI 来协调多个工具的调用。

### Q: 如何处理长时间运行的工具？

A: 有几种策略：

1. **设置超时**：使用 `asyncio.wait_for`
2. **异步执行**：返回任务 ID，提供查询状态的工具
3. **流式返回**：逐步返回中间结果
4. **拆分任务**：将长任务拆分为多个小任务

### Q: 工具返回的内容有大小限制吗？

A: 虽然没有硬性限制，但建议：

- 文本内容控制在 10KB 以内
- 对于大量数据，返回摘要或分页
- 使用 `brief` 字段提供简短说明

### Q: 如何调试工具？

A: 几种调试方法：

1. **单元测试**：独立测试工具逻辑
2. **日志记录**：记录工具的输入输出
3. **Mock Provider**：使用 Mock 测试工具集成
4. **打印调试**：在开发时打印中间结果

```python
async def __call__(self, params: SomeParams) -> ToolReturnType:
    logger.debug(f"工具调用: {self.name}, 参数: {params}")
    
    try:
        result = await self._execute(params)
        logger.debug(f"工具成功: {self.name}, 结果: {result}")
        return ToolOk(output=result)
    except Exception as e:
        logger.error(f"工具失败: {self.name}, 错误: {e}", exc_info=True)
        return ToolError(message=str(e), brief="执行失败")
```

### Q: 工具可以有副作用吗？

A: 可以，但要谨慎：

- **读操作**：通常是安全的（查询数据库、读文件）
- **写操作**：需要特别小心（修改数据、发送邮件）
- **建议**：对于有副作用的操作，在工具描述中明确说明，并考虑添加确认机制

## 下一步

- 学习[多轮对话](./multi-turn-conversation.md)在对话中使用工具
- 学习[流式输出](./streaming-output.md)实时显示工具执行过程
- 学习[错误处理](./error-handling.md)提高工具的健壮性
- 阅读[生产部署](./production-deployment.md)准备上线

## 相关资源

- [API 参考 - Tooling](../api-reference/tooling.md)
- [API 参考 - step](../api-reference/step.md)
- [API 参考 - generate](../api-reference/generate.md)
- [核心概念](../core-concepts.md)

