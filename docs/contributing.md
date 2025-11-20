# 贡献指南

感谢您对 Kosong 项目的关注！我们欢迎所有形式的贡献，包括但不限于：

- 报告 Bug
- 提出新功能建议
- 改进文档
- 提交代码修复或新功能
- 优化性能

本指南将帮助您了解如何参与 Kosong 项目的开发。

## 开发环境设置

### 前置要求

- Python 3.13 或更高版本
- [uv](https://docs.astral.sh/uv/) 包管理器（推荐）

### 克隆仓库

首先，Fork 本仓库到您的 GitHub 账户，然后克隆到本地：

```bash
git clone https://github.com/YOUR_USERNAME/kosong.git
cd kosong
```

### 安装依赖

使用 uv 安装项目依赖和开发依赖：

```bash
# 安装所有依赖（包括开发依赖）
uv sync --all-groups
```

这将安装以下依赖：

**运行时依赖：**
- anthropic (>=0.72.0)
- jsonschema (>=4.25.1)
- loguru (>=0.7.3)
- openai (>=2.6.1, <2.7.0)
- pydantic (>=2.12.4)
- python-dotenv (>=1.2.1)

**开发依赖：**
- pyright (>=1.1.407) - 类型检查
- pytest (>=8.4.2) - 测试框架
- pytest-asyncio (>=1.2.0) - 异步测试支持
- ruff (>=0.14.4) - 代码格式化和 linting
- inline-snapshot (>=0.31.1) - 快照测试
- pdoc (>=16.0.0) - 文档生成

### 配置开发工具

#### Pyright 配置

项目已包含 `pyrightconfig.json` 配置文件，启用了严格的类型检查：

```json
{
    "typeCheckingMode": "strict",
    "pythonVersion": "3.13",
    "include": [
        "src/**/*.py",
        "tests/**/*.py"
    ],
    "exclude": [
        "**/__pycache__/**/*.py"
    ]
}
```

在您的编辑器中配置 Pyright 以获得实时类型检查支持。

#### Ruff 配置

项目使用 Ruff 进行代码格式化和 linting。配置位于 `pyproject.toml`：

```toml
[tool.ruff]
line-length = 100

[tool.ruff.format]
docstring-code-format = true

[tool.ruff.lint]
select = [
    "E",   # pycodestyle
    "F",   # Pyflakes
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "SIM", # flake8-simplify
    "I",   # isort
]
```

#### 验证环境设置

运行以下命令验证开发环境是否正确配置：

```bash
# 运行代码检查
make check

# 运行测试
make test
```

如果所有检查都通过，说明您的开发环境已准备就绪。

## 代码规范

为了保持代码库的一致性和可维护性，请遵循以下代码规范。

### 代码风格

项目使用 Ruff 进行代码格式化和 linting。在提交代码前，请运行：

```bash
# 自动修复格式问题
make format

# 检查代码风格
make check
```

**关键规则：**
- 每行最多 100 个字符
- 使用 4 个空格缩进（不使用 Tab）
- 文档字符串中的代码示例也会被格式化
- 遵循 PEP 8 风格指南
- 使用 isort 对导入语句排序

### 命名约定

遵循 Python 社区的标准命名约定：

**模块和包：**
- 使用小写字母和下划线：`chat_provider.py`, `tool_execution.py`

**类名：**
- 使用 PascalCase（大驼峰）：`ChatProvider`, `ToolResult`, `MessagePart`

**函数和方法：**
- 使用 snake_case（小写+下划线）：`generate()`, `execute_tool()`, `parse_message()`

**常量：**
- 使用全大写字母和下划线：`MAX_RETRIES`, `DEFAULT_TIMEOUT`

**私有成员：**
- 使用单下划线前缀：`_internal_method()`, `_cache`

**类型变量：**
- 使用简短的 PascalCase 名称：`T`, `ParamsT`, `ReturnT`

### 类型注解要求

Kosong 使用严格的类型检查（Pyright strict mode）。所有代码必须包含完整的类型注解：

**函数签名：**
```python
# ✅ 正确
async def generate(
    chat_provider: ChatProvider,
    system_prompt: str,
    tools: list[Tool],
    history: list[Message],
) -> GenerateResult:
    ...

# ❌ 错误 - 缺少类型注解
async def generate(chat_provider, system_prompt, tools, history):
    ...
```

**变量注解：**
```python
# ✅ 正确 - 当类型不明显时添加注解
message_parts: list[MessagePart] = []
result: ToolResult | None = None

# ✅ 正确 - 类型明显时可以省略
count = 0
name = "kosong"
```

**泛型使用：**
```python
# ✅ 正确 - 使用具体的泛型类型
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

### 文档字符串格式

使用 Google 风格的文档字符串，并包含类型信息：

```python
async def execute_tool(
    tool: Tool,
    params: dict[str, Any],
    timeout: float = 30.0,
) -> ToolResult:
    """执行工具调用并返回结果。

    Args:
        tool: 要执行的工具实例
        params: 工具参数字典
        timeout: 执行超时时间（秒），默认 30 秒

    Returns:
        工具执行结果，包含输出或错误信息

    Raises:
        TimeoutError: 当工具执行超时时
        ValidationError: 当参数验证失败时

    Example:
        ```python
        tool = AddTool()
        params = {"a": 1, "b": 2}
        result = await execute_tool(tool, params)
        print(result.output)  # "3"
```text
    """
    ...
```

**文档字符串要求：**
- 所有公共 API 必须有文档字符串
- 包含简短的功能描述
- 使用 `Args:` 说明参数
- 使用 `Returns:` 说明返回值
- 使用 `Raises:` 说明可能抛出的异常
- 提供使用示例（当适用时）
- 文档字符串中的代码示例会被 Ruff 自动格式化

### 代码组织

**导入顺序：**
1. 标准库导入
2. 第三方库导入
3. 本地模块导入

每组之间用空行分隔，Ruff 会自动排序：

```python
import asyncio
from typing import Any

from pydantic import BaseModel

from kosong.message import Message
from kosong.tooling import Tool
```

**模块结构：**
```python
"""模块文档字符串。"""

# 导入语句
import ...

# 类型定义和常量
T = TypeVar("T")
MAX_RETRIES = 3

# 类定义
class MyClass:
    ...

# 函数定义
def my_function():
    ...
```

## 测试要求

Kosong 使用 pytest 作为测试框架，并使用 pytest-asyncio 支持异步测试。

### 运行测试

```bash
# 运行所有测试
make test

# 或直接使用 pytest
uv run pytest --doctest-modules -vv

# 运行特定测试文件
uv run pytest tests/test_generate.py -vv

# 运行特定测试函数
uv run pytest tests/test_generate.py::test_generate -vv
```

### 编写单元测试

**测试文件组织：**
- 测试文件放在 `tests/` 目录下
- 测试文件名以 `test_` 开头：`test_generate.py`, `test_tooling.py`
- 测试函数名以 `test_` 开头：`test_generate()`, `test_tool_execution()`

**同步测试示例：**
```python
def test_message_creation():
    """测试消息对象的创建。"""
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == [TextPart(text="Hello")]
```

**异步测试示例：**
```python
import asyncio
from kosong import generate
from kosong.chat_provider.mock import MockChatProvider

def test_generate():
    """测试 generate 函数的基本功能。"""
    chat_provider = MockChatProvider(
        message_parts=[TextPart(text="Hello, world!")]
    )
    
    result = asyncio.run(
        generate(
            chat_provider=chat_provider,
            system_prompt="You are helpful.",
            tools=[],
            history=[],
        )
    )
    
    assert result.message.content == [TextPart(text="Hello, world!")]
```

**使用 pytest-asyncio：**
```python
import pytest
from kosong import step
from kosong.tooling.simple import SimpleToolset

@pytest.mark.asyncio
async def test_tool_execution():
    """测试工具执行流程。"""
    toolset = SimpleToolset()
    toolset += MyTool()
    
    result = await step(
        chat_provider=chat_provider,
        system_prompt="",
        toolset=toolset,
        history=[Message(role="user", content="Use the tool")],
    )
    
    tool_results = await result.tool_results()
    assert len(tool_results) > 0
```

### 测试覆盖率要求

虽然我们不强制要求 100% 的测试覆盖率，但请确保：

- **核心功能必须有测试**：`generate()`, `step()`, 工具执行等
- **新功能必须包含测试**：添加新功能时，请同时添加相应的测试
- **Bug 修复应包含回归测试**：修复 Bug 时，添加测试以防止问题再次出现
- **公共 API 必须有测试**：所有导出的类和函数都应该有测试覆盖

### 测试最佳实践

**使用 Mock 对象：**
```python
from kosong.chat_provider.mock import MockChatProvider

# 使用 MockChatProvider 避免真实 API 调用
chat_provider = MockChatProvider(
    message_parts=[TextPart(text="Mocked response")]
)
```

**测试边界情况：**
```python
def test_empty_history():
    """测试空历史记录的处理。"""
    result = asyncio.run(generate(chat_provider, "", [], []))
    assert result.message is not None

def test_invalid_tool_params():
    """测试无效工具参数的处理。"""
    with pytest.raises(ValidationError):
        tool = AddTool()
        asyncio.run(tool(AddToolParams(a="not_a_number", b=2)))
```

**保持测试独立：**
- 每个测试应该独立运行
- 不依赖其他测试的执行顺序
- 使用 fixtures 共享测试设置

**测试命名清晰：**
```python
# ✅ 好的测试名称
def test_generate_with_streaming_callback():
    ...

def test_tool_execution_timeout_error():
    ...

# ❌ 不好的测试名称
def test_1():
    ...

def test_stuff():
    ...
```

### Doctest

项目启用了 doctest，文档字符串中的代码示例会被测试：

```python
def add(a: int, b: int) -> int:
    """将两个整数相加。

    Example:
        >>> add(2, 3)
        5
        >>> add(-1, 1)
        0
    """
    return a + b
```

确保文档字符串中的示例代码是正确的，因为它们会在测试时执行。

## 贡献流程

### 提交 Issue

在开始编写代码之前，建议先创建一个 Issue 来讨论您的想法：

**报告 Bug：**
1. 搜索现有 Issues，确认问题尚未被报告
2. 创建新 Issue，使用清晰的标题
3. 提供以下信息：
   - Bug 的详细描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（Python 版本、操作系统等）
   - 相关的代码片段或错误日志

**提出新功能：**
1. 搜索现有 Issues，确认功能尚未被提出
2. 创建新 Issue，描述：
   - 功能的用途和价值
   - 预期的 API 设计
   - 可能的实现方案
   - 是否愿意自己实现

### Fork 和分支策略

**Fork 仓库：**
1. 在 GitHub 上 Fork 本仓库
2. 克隆您的 Fork 到本地
3. 添加上游仓库为 remote：
   ```bash
   git remote add upstream https://github.com/original/kosong.git
   ```

**创建功能分支：**
```bash
# 从最新的 main 分支创建新分支
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name

# 或修复 Bug
git checkout -b fix/bug-description
```

**分支命名约定：**
- `feature/` - 新功能：`feature/add-gemini-provider`
- `fix/` - Bug 修复：`fix/tool-timeout-error`
- `docs/` - 文档改进：`docs/update-contributing-guide`
- `refactor/` - 代码重构：`refactor/simplify-message-parsing`
- `test/` - 测试改进：`test/add-streaming-tests`

### 开发工作流

1. **在功能分支上开发：**
   ```bash
   # 进行代码修改
   # 运行测试确保没有破坏现有功能
   make test
   
   # 运行代码检查
   make check
   
   # 自动修复格式问题
   make format
   ```

2. **提交代码：**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   **提交信息格式：**
   - `feat:` - 新功能
   - `fix:` - Bug 修复
   - `docs:` - 文档更新
   - `style:` - 代码格式调整（不影响功能）
   - `refactor:` - 代码重构
   - `test:` - 测试相关
   - `chore:` - 构建或辅助工具的变动

   示例：
```text
   feat: add support for Gemini chat provider
   
   - Implement GeminiChatProvider class
   - Add streaming support
   - Add tests for Gemini provider
   ```

3. **保持分支更新：**
   ```bash
   # 定期同步上游更改
   git fetch upstream
   git rebase upstream/main
   ```

### 提交 Pull Request

当您的功能开发完成后，可以提交 Pull Request (PR)：

1. **推送分支到您的 Fork：**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **在 GitHub 上创建 Pull Request：**
   - 访问您的 Fork 仓库页面
   - 点击 "Compare & pull request" 按钮
   - 填写 PR 描述

3. **PR 描述应包含：**
   - 变更的简要说明
   - 相关的 Issue 编号（如 `Closes #123`）
   - 测试说明
   - 截图或示例（如适用）
   - 破坏性变更说明（如有）

   **PR 模板示例：**
   ```markdown
   ## 描述
   添加了对 Gemini API 的支持，允许用户使用 Google 的 Gemini 模型。

   ## 相关 Issue
   Closes #45

   ## 变更类型
   - [x] 新功能
   - [ ] Bug 修复
   - [ ] 文档更新
   - [ ] 代码重构

   ## 测试
   - [x] 添加了单元测试
   - [x] 所有现有测试通过
   - [x] 手动测试通过

   ## 检查清单
   - [x] 代码遵循项目的代码规范
   - [x] 添加了必要的文档
   - [x] 更新了 CHANGELOG.md
   - [x] 没有引入破坏性变更
   ```

4. **确保 PR 通过所有检查：**
   - 所有测试通过
   - 代码风格检查通过
   - 类型检查通过
   - 没有合并冲突

### 代码审查流程

提交 PR 后，维护者会进行代码审查：

1. **审查过程：**
   - 维护者会检查代码质量、测试覆盖率和文档
   - 可能会提出修改建议或问题
   - 请及时回复评论并进行必要的修改

2. **响应审查意见：**
   ```bash
   # 根据反馈进行修改
   git add .
   git commit -m "address review comments"
   git push origin feature/your-feature-name
   ```

3. **合并：**
   - 当所有审查意见都被解决后，维护者会合并您的 PR
   - 合并后，您可以删除功能分支：
     ```bash
     git branch -d feature/your-feature-name
     git push origin --delete feature/your-feature-name
     ```

### 审查标准

PR 需要满足以下标准才能被合并：

- ✅ 代码功能正确，没有明显的 Bug
- ✅ 包含充分的测试覆盖
- ✅ 遵循项目的代码规范
- ✅ 类型注解完整，通过 Pyright 检查
- ✅ 包含必要的文档和注释
- ✅ 提交信息清晰明确
- ✅ 没有不必要的文件或代码
- ✅ 与现有代码风格一致

## 其他贡献方式

### 改进文档

文档改进同样重要：

- 修正拼写或语法错误
- 改进现有文档的清晰度
- 添加更多示例
- 翻译文档到其他语言

文档位于 `docs/` 目录，使用 Markdown 格式。

### 帮助其他用户

- 在 Issues 中回答问题
- 在讨论区分享使用经验
- 编写教程或博客文章
- 在社交媒体上推广项目

### 报告安全问题

如果您发现安全漏洞，请不要公开提交 Issue。请通过私密方式联系维护者。

## 行为准则

参与本项目时，请遵循以下准则：

- 尊重所有贡献者
- 接受建设性的批评
- 关注对社区最有利的事情
- 对其他社区成员表现出同理心

## 获取帮助

如果您在贡献过程中遇到问题：

- 查看现有的文档和 Issues
- 在 Issue 中提问
- 联系维护者

## 许可证

通过向本项目贡献代码，您同意您的贡献将按照项目的许可证进行授权。

---

再次感谢您对 Kosong 项目的贡献！我们期待与您合作。
