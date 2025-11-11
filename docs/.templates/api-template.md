---
title: API 名称
description: API 简短描述
version: 0.23.0
last_updated: YYYY-MM-DD
---

# API 名称

> API 的简短说明和用途。

## 函数签名 / 类定义

```python
def function_name(
    param1: Type1,
    param2: Type2,
    *,
    optional_param: Type3 = default_value,
) -> ReturnType:
    """函数的文档字符串。"""
    ...
```

或

```python
class ClassName:
    """类的文档字符串。"""
    
    def method_name(self, param: Type) -> ReturnType:
        """方法的文档字符串。"""
        ...
```

## 参数说明

### 必需参数

- **param1** (`Type1`): 参数说明
- **param2** (`Type2`): 参数说明

### 可选参数

- **optional_param** (`Type3`, 默认值: `default_value`): 参数说明

## 返回值

**类型：** `ReturnType`

返回值的详细说明。

## 异常

- **ExceptionType1**: 异常触发条件和说明
- **ExceptionType2**: 异常触发条件和说明

## 使用示例

### 示例 1：基础用法

```python
# 示例标题

import asyncio

async def main() -> None:
    result = await function_name(param1, param2)
    print(result)

asyncio.run(main())
```

**输出：**
```
预期输出内容
```

### 示例 2：高级用法

```python
# 高级用法示例

import asyncio

async def main() -> None:
    result = await function_name(
        param1,
        param2,
        optional_param=custom_value,
    )
    print(result)

asyncio.run(main())
```

## 注意事项

- 重要的使用注意事项
- 性能考虑
- 最佳实践建议

## 相关 API

- [相关 API 1](./related-api-1.md)
- [相关 API 2](./related-api-2.md)

---

_文档版本: v0.23.0 | 最后更新: YYYY-MM-DD_
