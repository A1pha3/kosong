#!/usr/bin/env python3
"""
提取并验证文档中的代码示例

从文档中提取 Python 代码示例并尝试验证其语法正确性
"""

import re
import ast
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple


class CodeExampleExtractor:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.examples: Dict[str, List[Tuple[int, str]]] = {}
        self.issues: Dict[str, List[str]] = {}
    
    def extract_all(self) -> Dict[str, List[Tuple[int, str]]]:
        """从所有文档中提取代码示例"""
        md_files = list(self.docs_dir.rglob("*.md"))
        
        # 排除模板文件
        md_files = [f for f in md_files if ".templates" not in str(f)]
        
        for md_file in md_files:
            examples = self.extract_from_file(md_file)
            if examples:
                self.examples[str(md_file)] = examples
        
        return self.examples
    
    def extract_from_file(self, file_path: Path) -> List[Tuple[int, str]]:
        """从单个文件中提取 Python 代码示例"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            examples = []
            in_python_block = False
            current_example = []
            start_line = 0
            
            for i, line in enumerate(lines, 1):
                if line.strip().startswith("```python"):
                    in_python_block = True
                    start_line = i
                    current_example = []
                elif line.strip() == "```" and in_python_block:
                    in_python_block = False
                    if current_example:
                        code = "\n".join(current_example)
                        examples.append((start_line, code))
                elif in_python_block:
                    current_example.append(line)
            
            return examples
        
        except Exception as e:
            print(f"❌ 错误读取 {file_path}: {e}")
            return []
    
    def validate_all(self) -> None:
        """验证所有提取的代码示例"""
        total_examples = sum(len(examples) for examples in self.examples.values())
        print(f"📊 共提取 {total_examples} 个 Python 代码示例\n")
        
        for file_path, examples in self.examples.items():
            file_issues = []
            
            for line_num, code in examples:
                issues = self.validate_code(code, line_num)
                if issues:
                    file_issues.extend(issues)
            
            if file_issues:
                self.issues[file_path] = file_issues
    
    def validate_code(self, code: str, line_num: int) -> List[str]:
        """验证单个代码示例的语法"""
        issues = []
        
        # 跳过明显的代码片段（不完整的代码）
        if self.is_code_snippet(code):
            return issues
        
        # 尝试解析 Python 语法
        try:
            ast.parse(code)
        except SyntaxError as e:
            # 如果是缩进错误，尝试去除前导空格后再解析
            if "indent" in e.msg.lower():
                try:
                    # 去除所有行的公共前导空格
                    dedented_code = self.dedent_code(code)
                    ast.parse(dedented_code)
                    # 如果去除缩进后能解析，说明这是嵌套在列表中的代码块，是正常的
                    return issues
                except:
                    pass
            
            issues.append(f"Line {line_num}: 语法错误 - {e.msg} (行 {e.lineno})")
        except Exception as e:
            # 其他解析错误通常是因为代码片段不完整，可以忽略
            pass
        
        return issues
    
    def dedent_code(self, code: str) -> str:
        """去除代码的公共前导空格"""
        lines = code.split("\n")
        # 找到最小的非空行缩进
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        if min_indent == float('inf'):
            return code
        
        # 去除公共缩进
        dedented_lines = []
        for line in lines:
            if line.strip():
                dedented_lines.append(line[min_indent:])
            else:
                dedented_lines.append(line)
        
        return "\n".join(dedented_lines)
    
    def is_code_snippet(self, code: str) -> bool:
        """判断是否是代码片段（不完整的代码）"""
        code_stripped = code.strip()
        
        # 检查是否是明显的代码片段
        snippet_indicators = [
            code_stripped.startswith("..."),
            code_stripped.endswith("..."),
            "# ..." in code,
            code.count("\n") < 3,  # 少于3行通常是片段
            # 以这些关键字开头的通常是代码片段
            code_stripped.startswith("except "),
            code_stripped.startswith("elif "),
            code_stripped.startswith("else:"),
            code_stripped.startswith("finally:"),
            code_stripped.startswith("return "),
            code_stripped.startswith("yield "),
            code_stripped.startswith("break"),
            code_stripped.startswith("continue"),
        ]
        
        return any(snippet_indicators)
    
    def print_report(self) -> None:
        """打印验证报告"""
        if not self.issues:
            print("✅ 所有代码示例语法检查通过！")
            return
        
        print(f"⚠️  发现 {len(self.issues)} 个文件存在代码问题：\n")
        
        total_issues = 0
        for file_path, issues in sorted(self.issues.items()):
            print(f"📄 {file_path}")
            for issue in issues:
                print(f"   - {issue}")
                total_issues += 1
            print()
        
        print(f"总计: {total_issues} 个问题")
    
    def print_statistics(self) -> None:
        """打印统计信息"""
        total_files = len(self.examples)
        total_examples = sum(len(examples) for examples in self.examples.values())
        
        print(f"\n📈 统计信息:")
        print(f"   - 文档文件数: {total_files}")
        print(f"   - 代码示例数: {total_examples}")
        print(f"   - 有问题的文件: {len(self.issues)}")


def main():
    extractor = CodeExampleExtractor()
    extractor.extract_all()
    extractor.validate_all()
    extractor.print_report()
    extractor.print_statistics()


if __name__ == "__main__":
    main()
