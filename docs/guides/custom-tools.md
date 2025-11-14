---
title: 自定义工具指南
description: 学习如何创建和使用自定义工具来扩展 AI Agent 的能力
version: 0.23.0
last_updated: 2025-01-15
---

# 自定义工具指南

工具（Tool）是 AI Agent 与外部世界交互的桥梁。通过自定义工具，你可以让 AI 执行各种操作，如查询数据库、调用 API、执行计算等。本指南将介绍如何使用 Kosong 创建强大且可靠的自定义工具。

## 场景说明

自定义工具可以应用于各种场景：

- **数据查询**：让 AI 查询数据库、搜索文档或访问 API
- **计算和处理**：执行复杂计算、数据转换或文件处理
- **外部集成**：与第三方服务集成，如发送邮件、创建任务等
- **系统操作**：执行系统命令、管理文件或配置系统

## 核心概念

Kosong 提供两种方式创建自定义工具：

1. **CallableTool**：使用 JSON Schema 定义参数的传统方式
2. **CallableTool2**：使用 Pydantic 模型定义参数的现代方式（推荐）

工具的返回值必须是 `ToolOk`（成功）或 `ToolError`（错误），这样可以让 AI 理解工具执行的结果。

## 快速开始：创建第一个工具

让我们从一个简单的天气查询工具开始：

```python
import asyncio

from pydantic import BaseModel, Field

import kosong
from kosong.chat_provider.kimi import Kimi
from kosong.message import Message
from kosong.tooling import CallableTool2, ToolOk, ToolReturnType
from kosong.tooling.simple import SimpleToolset


# 1. 定义工具参数模型
class WeatherParams(BaseModel):
    city: str = Field(description="要查询天气的城市名称")


# 2. 创建工具类
class WeatherTool(CallableTool2[WeatherParams]):
    name: str = "get_weather"
    description: str = "查询指定城市的天气信息"
    params: type[WeatherParams] = WeatherParams

    async def __call__(self, params: WeatherParams) -> ToolReturnType:
