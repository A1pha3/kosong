---
title: 指南标题
description: 指南简短描述
version: 0.23.0
last_updated: YYYY-MM-DD
---

# 指南标题

> 简短说明本指南的目标和适用场景。

## 场景说明

详细描述本指南要解决的实际问题或应用场景。

**适用于：**
- 使用场景 1
- 使用场景 2
- 使用场景 3

## 前置知识

在开始本指南前，建议先了解：

- [相关概念 1](../core-concepts.md)
- [相关 API 1](../api-reference/api-name.md)

## 完整示例

### 步骤 1：准备工作

说明需要做的准备工作。

```python
# 准备代码
import asyncio
from kosong import generate

# 配置
API_KEY = "your_api_key_here"
```

### 步骤 2：核心实现

```python
# 核心实现代码

async def main() -> None:
    # 实现逻辑
    result = await generate(...)
    print(result)

asyncio.run(main())
```

**说明：**
- 关键代码解释
- 工作原理说明

### 步骤 3：运行和测试

```bash
# 运行命令
python example.py
```

**预期输出：**
```
输出内容示例
```

## 进阶技巧

### 技巧 1：优化方案

说明和代码示例...

### 技巧 2：错误处理

说明和代码示例...

## 常见问题

### 问题 1：如何处理 XXX？

解答和示例代码...

### 问题 2：为什么会出现 YYY？

解答和示例代码...

## 最佳实践

1. **实践 1**：说明和建议
2. **实践 2**：说明和建议
3. **实践 3**：说明和建议

## 完整代码示例

```python
# 完整的可运行示例

import asyncio
from kosong import generate

async def main() -> None:
    # 完整实现
    pass

if __name__ == "__main__":
    asyncio.run(main())
```

## 下一步

- [相关指南 1](./related-guide-1.md)
- [相关指南 2](./related-guide-2.md)
- [高级主题](../advanced/README.md)

---

_文档版本: v0.23.0 | 最后更新: YYYY-MM-DD_
